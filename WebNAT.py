from telnet_router import TelnetClient
from flask import Flask, request
from flask_restplus import Api, Resource, fields
from urllib import parse
from ConnectionDAO import ConnectionDAO

app = Flask(__name__)

api = Api(app, version='1.0', title='WebNAT API',
    description='Network NAT Web API',
)

# 定义命名空间
ns = api.namespace('NAT', description='NAT operations')

ip_address_fields = api.model('IPAddress', {
    'ip': fields.String,
    'netmask': fields.String,
    'mask_bit': fields.Integer
})

ip_address_combined = api.model('IPAddressCombined', {
    'primary': fields.Nested(ip_address_fields),
    'secondary': fields.List(fields.Nested(ip_address_fields))
})

interface = api.model('Interface', {
    'name': fields.String(description='Name of the interface'),
    'abbr': fields.String(description='Abbreviation of the interface'),
    'ip_address': fields.Nested(ip_address_combined),
    'is_open': fields.Boolean
})

hostname = api.model('Hostname', {
    'hostname': fields.String,
})

DAO = ConnectionDAO()
router_ips = ['172.16.0.2','172.16.0.3','172.16.0.4']

@ns.route('/telnet')
class TelnetConnect(Resource):
    @ns.doc('TelnetConnect')
    @ns.param('router_id', 'The router identifier')
    def post(self):
        '''创建一个新的路由器连接'''
        router_id = int(request.args.get("router_id"))
        tc = TelnetClient()
        tc.login(router_ips[router_id-1], 'root', 'cisco')
        tc.switch_root('cisco')
        return DAO.add(tc)

@ns.route('/exit')
class TelnetDisconnect(Resource):
    @ns.doc('TelnetDisconnect')
    @ns.param('connection_id', 'The connection identifier')
    def post(self):
        '''断开一个已有的路由器连接'''
        connection_id = int(request.args.get("connection_id"))
        DAO.delete(connection_id)

@ns.route('/hostname')
@ns.param('connection_id', 'The connection identifier')
class Hostname(Resource):
    @ns.doc('GetHostname')
    def get(self):
        '''获取主机名'''
        connection_id = int(request.args.get("connection_id"))
        return DAO.get(connection_id).get_hostname()
    
    @ns.doc('SetHostname')
    @ns.expect(hostname)
    def post(self):
        '''设置主机名'''
        connection_id = int(request.args.get("connection_id"))
        hostname = api.payload['hostname']
        return DAO.get(connection_id).set_hostname(hostname)

@ns.route('/interface')
@ns.param('connection_id', 'The connection identifier')
class InterfaceInfo(Resource):
    @ns.doc('GetInterfaceInfo')
    @ns.param('abbr', 'The abbreviation of interface')
    @ns.marshal_with(interface)
    def get(self):
        '''获取接口信息'''
        '''/作为路径参数传递时需要使用html编码%2f'''
        connection_id = int(request.args.get("connection_id"))
        abbr = parse.unquote(request.args.get("abbr"))
        return DAO.get(connection_id).get_interface_info(abbr)
        # return {
	    #     'name': 'FastEthernet0/0',
        #     'abbr': abbr,
        #     'ip_address': {
        #     'primary': { 'ip': '172.16.0.2', 'netmask': '255.255.255.0', 'mask_bit': 24 },
        #     'secondary': []
        #     },
        #     'is_open': True
        # }

    @ns.doc('SetInterfaceInfo')
    @ns.expect(interface)
    def post(self):
        '''设置接口信息'''
        connection_id = int(request.args.get("connection_id"))
        return DAO.get(connection_id).set_interface(api.payload)
    

if __name__ == '__main__':
    app.run(debug=True)