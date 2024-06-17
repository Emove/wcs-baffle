from flask import Flask, request
from gevent import pywsgi

import logger
import rms
from config.rms import get_rms_config, RMSConfig

_wcs = Flask(__name__)


def serve(port: int):
    _wcs_server = pywsgi.WSGIServer(("0.0.0.0", port), _wcs)
    logger.info(f"wcs-baffle serve on port: {port}")
    _wcs_server.serve_forever(stop_timeout=0)


@_wcs.route("/api/wcs/station/full", methods=["GET"])
def station_full():
    req_data = request.json
    logger.info(f"station is_full request: {req_data}.")
    station_id = req_data.get("station_id")
    if not station_id:
        return {"code": 1, "msg": "参数错误: station_id不能为空"}
    return {"code": 0, "is_full": True}


@_wcs.route("/api/wcs/station/prepare", methods=["POST"])
def station_prepare():
    req_data = request.json
    logger.info(f"station prepare request: {req_data}.")
    serial = req_data.get("serial")
    robot_type = req_data.get("robot_type")
    station_id = req_data.get("station_id")
    if serial is None:
        return {"code": 1, "msg": "参数错误: serial不能为空"}
    if robot_type is None:
        return {"code": 1, "msg": "参数错误: robot_type不能为空"}
    if station_id is None:
        return {"code": 1, "msg": "参数错误: station_id不能为空"}
    __submit_dock_prepare_callback(serial, station_id, robot_type)
    return {"code": 0, "msg": "站点准备中"}


@_wcs.route("/api/wcs/inbound/order_materials/inboundstart", methods=["POST"])
def inbound_start():
    data = request.json
    logger.info(f"The inbound start request: {data}.")
    station_id = data.get("station_id")
    serial = data.get("serial")
    robot_type = data.get("robot_type")
    if serial is None:
        return {"code": 1, "msg": "参数错误: serial不能为空"}
    if robot_type is None:
        return {"code": 1, "msg": "参数错误: robot_type不能为空"}
    if station_id is None:
        return {"code": 1, "msg": "参数错误: station_id不能为空"}
    __submit_dock_finish_callback(serial, station_id)
    return {"code": 0, "msg": "机器人对接开始"}


@_wcs.route("/api/wcs/inbound/order_materials/checkM1100", methods=["POST"])
def inbound_robot_left():
    data = request.json
    logger.info(f"The inbound robot left request: {data}.")
    station_id = data.get("station_id")
    robot_type = data.get("robot_type")
    if robot_type is None:
        return {"code": 1, "msg": "参数错误: robot_type不能为空"}
    if station_id is None:
        return {"code": 1, "msg": "参数错误: station_id不能为空"}
    return {"code": 0, "msg": "机器人离开接驳站处理成功"}


@_wcs.route("/api/wcs/putup", methods=["POST"])
def material_inbound_finished():
    materials_data = request.json
    logger.info(f"The material inbound finished request: {materials_data}.")
    order_id = materials_data.get("order_id")
    boxnumber = materials_data.get("boxnumber")
    location = materials_data.get("location")
    if order_id and boxnumber and location:
        logger.info(f"The order_id: {order_id}, boxnumber: {boxnumber}, location: {location}")
    return {"code": 0, "msg": "料箱入库完成!"}


# WCS-PLC出库
@_wcs.route("/api/wcs/outbound/order_materials/outboundready", methods=["POST"])
def outbound_workstation():
    data = request.json
    logger.info(f"The outbound workstation ready request: {data}.")
    station_id = data.get("station_id")
    if station_id is None:
        return {"code": 1, "msg": "参数错误: station_id不能为空"}
    return {"code": 0, "msg": "可执行出库"}


@_wcs.route("/api/wcs/outbound/order_materials/outboundstart", methods=["POST"])
def outbound_start():
    data = request.json
    order_id = data.get("order_id")
    tote_ids = data.get("tote_ids", [])
    station_id = data.get("station_id")
    serial = data.get("serial")
    robot_type = data.get("robot_type")
    logger.info(
        f"outbound_start, order_id: {order_id}, tote_ids: {tote_ids}, station_id: {station_id}, "
        f"serial: {serial}, robot_type: {robot_type}"
    )
    __submit_dock_finish_callback(serial, station_id)
    return {"code": 0, "msg": "出库执行中"}


@_wcs.route("/api/wcs/outbound/order_materials/checkM1108", methods=["POST"])
def outbound_robot_left():
    data = request.json
    logger.info(f"The outbound robot left request: {data}.")
    station_id = data.get("station_id")
    robot_type = data.get("robot_type")
    if robot_type is None:
        return {"code": 1, "msg": "参数错误: robot_type不能为空"}
    if station_id is None:
        return {"code": 1, "msg": "参数错误: station_id不能为空"}
    logger.info(f"机器人离开接驳站处理成功，station_id: {station_id}")
    return {"code": 0, "msg": "机器人离开接驳站处理成功"}


@_wcs.route("/api/wcs/mode/inbound", methods=["POST"])
def switch_to_inbound():
    data = request.json
    logger.info(f"switch to inbound mode request: {data}.")
    station_id = data.get("station_id")
    if station_id is None:
        return {"code": 1, "msg": "参数错误: station_id不能为空"}
    logger.info(f"切换接驳站为入库模式成功，station_id: {station_id}")
    return {"code": 0, "msg": "切换接驳站为入库模式成功"}


@_wcs.route("/api/wcs/mode/outbound", methods=["POST"])
def switch_to_outbound():
    data = request.json
    logger.info(f"switch to outbound mode request: {data}.")
    station_id = data.get("station_id")
    if station_id is None:
        return {"code": 1, "msg": "参数错误: station_id不能为空"}
    logger.info(f"切换接驳站为出库模式成功，station_id: {station_id}")
    return {"code": 0, "msg": "切换接驳站为出库模式成功"}


@_wcs.route("/api/wcs/inbound/stack/num", methods=["POST"])
def set_working_area_stack_num():
    data = request.json
    logger.info(f"set inbound working area stack num request: {data}.")
    station_id = data.get("station_id")
    if station_id is None:
        return {"code": 1, "msg": "参数错误: station_id不能为空"}
    return {"code": 0, "msg": "设置接驳站码垛箱数成功"}


@_wcs.route("/api/rms/demo", methods=["POST"])
def api_rms_demo():
    data = request.json
    logger.info(f"mock rms api received data: {data}.")
    return {"code": 0, "msg": ""}


def __submit_dock_prepare_callback(serial: str, station: str, robot_type: str):
    params = {
        "serial": serial,
        "station_id": station,
        "robot_type": robot_type,
    }
    rms_config = get_rms_config()
    rms.submit_delay_callback(rms_config.request.delay, get_url(rms_config, rms_config.apis.dock_ready), params)


def __submit_dock_finish_callback(serial: str, station: str):
    params = {
        "serial": serial,
        "station_id": station,
    }
    rms_config = get_rms_config()
    rms.submit_delay_callback(rms_config.request.delay, get_url(rms_config, rms_config.apis.dock_finish), params)


def get_url(rms_config: RMSConfig, url: str) -> str:
    return f"{rms_config.host}/{url}"
