import utils as u
from data import data as data_init
from flask import Flask, render_template, request, jsonify, make_response
from markupsafe import escape

# 初始化数据和Flask应用
d = data_init()
app = Flask(__name__)

# 错误返回的格式化函数
def reterr(code, message):
    ret = {
        'success': False,
        'code': code,
        'message': message
    }
    u.error('{} - {}'.format(code, message))  # 改为传统的格式化方式
    return u.format_dict(ret)

# 显示请求IP
def showip(req, msg):
    ip1 = req.remote_addr
    try:
        ip2 = req.headers['X-Forwarded-For']
        u.infon('- Request: {} / {} : {}'.format(ip1, ip2, msg))
    except KeyError:
        ip2 = None
        u.infon('- Request: {} : {}'.format(ip1, msg))

# 首页路由
@app.route('/')
def index():
    d.load()  # 加载数据
    showip(request, '/')  # 打印请求的IP和路径
    
    ot = d.data['other']
    
    # 获取设备类型
    device_type = request.args.get('device_type', 'unknown')  # 默认值为 unknown
    if device_type == 'phone':
        device_info = '手机端用户'
    elif device_type == 'computer':
        device_info = '电脑端用户'
    else:
        device_info = '未知设备类型'
    
    # 获取当前状态信息
    try:
        stat = next((s for s in d.data['status_list'] if s['id'] == d.data['status']), None)
        if stat is None:
            raise KeyError  # 如果没有找到对应的状态，则抛出异常
        
        if d.data['status'] == 0:
            app_name = d.data['app_name']
            # stat['name'] = app_name
    except KeyError:
        stat = {
            'name': '未知',
            'desc': '未知的标识符，可能是配置问题。',
            'color': 'error'
        }
    
    # 渲染首页模板，传递相关信息
    return render_template(
        'index.html',
        user=ot['user'],
        learn_more=ot['learn_more'],
        repo=ot['repo'],
        status_name=stat['name'],
        status_desc=stat['desc'],
        status_color=stat['color'],
        more_text=ot['more_text'],
        device_info=device_info,  # 传递设备类型信息
        phone_app=d.data.get('phone_app', '未知应用'),
        computer_app=d.data.get('computer_app', '未知应用')
    )

# 请求样式文件
@app.route('/style.css')
def style_css():
    response = make_response(render_template(
        'style.css',
        bg=d.data['other']['background'],
        alpha=d.data['other']['alpha']
    ))
    response.mimetype = 'text/css'
    return response

# 获取当前状态信息的API
@app.route('/query')
def query():
    d.load()
    showip(request, '/query')
    st = d.data['status']
    
    try:
        stinfo = d.data['status_list'][st]
        if st == 0:
            stinfo['name'] = d.data['app_name']
    except KeyError:
        stinfo = {
            'status': st,
            'name': '未知'
        }
    
    # 返回JSON格式的状态信息
    ret = {
        'success': True,
        'status': st,
        'info': stinfo
    }
    return u.format_dict(ret)

# 获取状态列表的API
@app.route('/get/status_list')
def get_status_list():
    showip(request, '/get/status_list')
    stlst = d.dget('status_list')
    return u.format_dict(stlst)

# 设置状态信息的API
@app.route('/set')
def set_normal():
    showip(request, '/set')
    
    # 获取传入的参数
    status = escape(request.args.get("status"))
    app_name = escape(request.args.get("app_name"))
    device_type = escape(request.args.get("device_type"))
    
    try:
        status = int(status)  # 尝试将status转换为整数
    except ValueError:
        return reterr(
            code='bad request',
            message="argument 'status' must be a number"
        )
    
    secret = escape(request.args.get("secret"))
    u.info('status: {}, name: {}, secret: "{}", device_type: "{}"'.format(status, app_name, secret, device_type))
    
    # 检查secret是否合法
    secret_real = d.dget('secret')

    if secret == secret_real:
        current_phone_status = d.data.get('phone_status', 0)
        current_computer_status = d.data.get('computer_status', 0)

        if device_type == 'phone':
            current_phone_status = status
            d.dset('phone_app', app_name)

        elif device_type == 'computer':
            current_computer_status = status
            d.dset('computer_app', app_name)

        # 进行与运算
        new_status = current_phone_status & current_computer_status
        d.dset('status', new_status)
        d.dset('phone_status', current_phone_status)
        d.dset('computer_status', current_computer_status)
        
        u.info('set success')
        
        ret = {
            'success': True,
            'code': 'OK',
            'set_to': new_status,
            'app_name': app_name
        }
        return u.format_dict(ret)
    else:
        return reterr(
            code='not authorized',
            message='invalid secret'
        )

# 启动Flask应用
if __name__ == '__main__':
    d.load()  # 加载数据
    app.run(
        host=d.data['host'],
        port=d.data['port'],
        debug=d.data['debug']
    )



