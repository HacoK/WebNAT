from telnet_router import TelnetClient
from flask import Flask, request
from flask_restplus import Api, Resource, fields
from urllib import parse

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


class ConnectionDAO(object):
    def __init__(self):
        self.counter = 0
        self.conections = {}

    def get(self, connection_id):
        return self.conections[connection_id]

    def add(self, telnet_client):
        self.counter += 1
        self.conections[self.counter] = telnet_client
        return self.counter

    def update(self, connection_id, telnet_client):
        self.conections[connection_id] = telnet_client

    def delete(self, connection_id):
        self.conections[connection_id].logout()
        del self.conections[connection_id]

DAO = ConnectionDAO()
router_ips = {'172.16.0.2','172.16.0.3','172.16.0.4'}

@ns.route('/telnet')
class TelnetConnect(Resource):
    @ns.doc('TelnetConnect')
    @ns.param('router_id', 'The router identifier')
    def post(self):
        '''创建一个新的路由器连接'''
        router_id = request.form['router_id']
        tc = TelnetClient()
        tc.login(router_ips[router_id-1], 'root', '123456')
        tc.switch_root('123456')
        return DAO.add(tc)

@ns.route('/exit')
class TelnetDisconnect(Resource):
    @ns.doc('TelnetDisconnect')
    @ns.param('connection_id', 'The connection identifier')
    def post(self):
        '''断开一个已有的路由器连接'''
        connection_id = request.form['connection_id']
        DAO.delete(connection_id)

@ns.route('/hostname/<int:connection_id>')
@ns.param('connection_id', 'The connection identifier')
class Hostname(Resource):
    @ns.doc('GetHostname')
    def get(self, connection_id):
        '''获取主机名'''
        return DAO.get(connection_id).get_hostname()
    
    @ns.doc('SetHostname')
    @ns.param('hostname', 'The hostname to set')
    def post(self, connection_id):
        '''设置主机名'''
        hostname = request.form['hostname']
        return DAO.get(connection_id).set_hostname(hostname)

@ns.route('/interface/<int:connection_id>/<string:abbr>')
@ns.param('connection_id', 'The connection identifier')
@ns.param('abbr', 'The abbreviation of interface')
class GetInterfaceInfo(Resource):
    @ns.doc('GetInterfaceInfo')
    @ns.marshal_with(interface)
    def get(self, connection_id, abbr):
        '''获取接口信息'''
        '''/作为路径参数传递时需要使用html编码%2f'''
        abbr = parse.unquote(abbr)
        # return {
	    #     'name': 'FastEthernet0/0',
        #     'abbr': abbr,
        #     'ip_address': {
        #     'primary': { 'ip': '172.16.0.2', 'netmask': '255.255.255.0', 'mask_bit': 24 },
        #     'secondary': []
        #     },
        #     'is_open': True
        # }
        return DAO.get(connection_id).get_interface_info(abbr)

@ns.route('/interface/<int:connection_id>')
@ns.param('connection_id', 'The connection identifier')
class SetInterface(Resource):
    @ns.doc('SetInterfaceInfo')
    @ns.expect(interface)
    def post(self, connection_id):
        '''设置接口信息'''
        return DAO.get(connection_id).set_interface(api.payload)

if __name__ == '__main__':
    app.run(debug=True)