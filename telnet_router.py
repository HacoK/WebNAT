import telnetlib
import time
from NetMaskHelper import exchange_maskint

class TelnetClient:
    def __init__(self):
        self.tn = telnetlib.Telnet()

    def input(self, cmd):
        self.tn.write(cmd.encode('ascii') + b'\n')

    def get_output(self, sleep_seconds=2):
        time.sleep(sleep_seconds)
        tmp = self.tn.read_very_eager().decode('ascii')
        if '--More--' in tmp.split('\r\n')[-1]:
            self.tn.write(b' ')
            time.sleep(sleep_seconds)
            tmp += self.tn.read_very_eager().decode('ascii')
        return tmp


    def login(self, host_ip, username, password):
        try:
            self.tn.open(host_ip)
        except:
            print('连接失败')
        #self.tn.read_until(b'login: ')
        #self.input(username)
        self.tn.read_until(b'Password: ')
        self.input(password)
        login_result = self.get_output()
        print(login_result)
        if 'Login incorrect' in login_result:
            print('用户名或密码错误')
            return False
        print('登陆成功')
        return True

    def logout(self):
        self.input('exit')

    def exec_cmd(self, cmd):
        self.input(cmd)
        res = self.get_output()
        print("===================")
        print(res)
        print("===================")
        return res

    def switch_root(self, password):
        self.exec_cmd('enable')
        self.input(password)
    
    def switch_normal(self):
        self.exec_cmd('disable')

    def get_hostname(self):
        return self.exec_cmd("").split('\r\n')[-1].strip()[:-1]

    def set_hostname(self, hostname):
        self.exec_cmd('configure terminal')
        result = self.exec_cmd('hostname ' + hostname)
        self.exec_cmd('exit')
        return result
    
    def set_interface(self, information):
        self.exec_cmd('configure terminal')
        self.exec_cmd('interface ' + information['abbr'])
        result = self.exec_cmd('ip address ' + information['ip_address']['primary']['ip'] + ' ' + information['ip_address']['primary']['netmask'])
        for secondary_ip in information['ip_address']['secondary']:
            result += self.exec_cmd('ip address ' + secondary_ip['ip'] + ' ' + secondary_ip['netmask'] + ' secondary')
        result += self.exec_cmd('no shutdown')
        if information['ip_nat']:
            result += self.exec_cmd('ip nat '+information['ip_nat'])
        self.exec_cmd('end')
        return result
    
    def get_interface_info(self, abbr):
        info = {}
        info['abbr'] = abbr
        info['name'] = abbr
        info['name'] = info['name'].replace("f", "FastEthernet")
        info['name'] = info['name'].replace("s", "Serial")
        '''根据show ip interface abbr输出补充ip_address以及is_open'''
        output = self.exec_cmd('show ip interface ' + abbr)
        info['is_open'] = True
        info['ip_nat'] = None
        info['ip_address'] = {'primary':{}, 'secondary':[]}
        for str in output.split('\r\n'):
            if 'down' in str:
                info['is_open'] = False
                return info
            if 'NAT Outside' in str:
                info['ip_nat'] = 'outside'
            if 'NAT Inside' in str:
                info['ip_nat'] = 'inside'
            if 'Internet address is' in str:
                str = str.split(' ')[-1]
                mask_bit = int(str.split('/')[1])
                netmask = exchange_maskint(mask_bit)
                info['ip_address']['primary']={ 'ip': str.split('/')[0], 'netmask': netmask, 'mask_bit': mask_bit }
            if 'Secondary address' in str:
                str = str.split(' ')[-1]
                mask_bit = int(str.split('/')[1])
                netmask = exchange_maskint(mask_bit)
                info['ip_address']['secondary'].append({ 'ip': str.split('/')[0], 'netmask': netmask, 'mask_bit': mask_bit })
        return info

    def get_NAT_table(self):
        result = self.exec_cmd('').strip()
        result += self.exec_cmd("show ip nat translations")
        return result

    def clear_NAT_table(self):
        result = self.exec_cmd('').strip()
        result += self.exec_cmd('clear ip nat translation *')
        return result

    def set_static_route(self):
        '''为R1加上去往R3的静态路由'''
        result = self.exec_cmd('').strip()
        result += self.exec_cmd('configure terminal')
        result += self.exec_cmd('ip route 200.1.1.0 255.255.255.0 s0/0/0')
        result += self.exec_cmd('end')
        return result

    def set_static_nat(self):
        '''在R2上完成静态NAT的配置'''
        result = self.exec_cmd('').strip()
        result += self.exec_cmd('configure terminal')
        result += self.exec_cmd('ip nat inside source static 192.168.1.1 200.1.1.254')
        result += self.exec_cmd('end')
        return result
        
    def delete_static_nat(self):
        '''在R2上删除静态NAT的配置'''
        result = self.exec_cmd('').strip()
        result += self.exec_cmd('configure terminal')
        result += self.exec_cmd('no ip nat inside source static 192.168.1.1 200.1.1.254')
        result += self.exec_cmd('end')
        return result

    def set_access_list(self):
        '''在R2上通过使用用户访问控制列表来定义本地地址池'''
        result = self.exec_cmd('').strip()
        result += self.exec_cmd('configure terminal')
        result += self.exec_cmd('access-list 1 permit 192.168.1.0 0.0.0.255')
        result += self.exec_cmd('end')
        return result

    def set_dynamic_nat(self):
        '''在R2上完成动态NAT的配置'''
        result = self.exec_cmd('').strip()
        result += self.exec_cmd('configure terminal')
        result += self.exec_cmd('ip nat pool nju 200.1.1.253 200.1.1.254 p 24')
        result += self.exec_cmd('ip nat inside source list 1 pool nju')
        result += self.exec_cmd('end')
        return result

    def delete_dynamic_nat(self):
        '''在R2上删除动态NAT的配置'''
        result = self.exec_cmd('').strip()
        result += self.exec_cmd('configure terminal')
        result += self.exec_cmd('no ip nat inside source list 1 pool nju')
        if '[no]' in result:
            result += self.exec_cmd('y')
        result += self.exec_cmd('no ip nat pool nju 200.1.1.253 200.1.1.254 p 24')
        result += self.exec_cmd('end')
        return result

    def set_PAT(self):
        '''在R2上完成PAT的配置'''
        result = self.exec_cmd('').strip()
        result += self.exec_cmd('configure terminal')
        result += self.exec_cmd('ip nat pool nju 200.1.1.253 200.1.1.253 p 24')
        result += self.exec_cmd('ip nat inside source list 1 pool nju overload')
        result += self.exec_cmd('end')
        return result

    def ping(self,target,source):
        result = self.exec_cmd('').strip()
        if source:
            '''执行Ping命令'''
            result += self.exec_cmd('ping')
            '''Protocol [ip]'''
            result += self.exec_cmd('')
            '''Target IP address'''
            result += self.exec_cmd(target)
            '''Repeat count [5]'''
            result += self.exec_cmd('')
            '''Datagram size [100]'''
            result += self.exec_cmd('')
            '''Timeout in seconds [2]'''
            result += self.exec_cmd('')
            '''Extended commands [n]'''
            result += self.exec_cmd('y')
            '''Source address or interface:'''
            result += self.exec_cmd(source)
            '''Type of service [0]'''
            result += self.exec_cmd('')
            '''Set DF bit in IP header? [no]'''
            result += self.exec_cmd('')
            '''Validate reply data? [no]'''
            result += self.exec_cmd('')
            '''Data pattern [0xABCD]'''
            result += self.exec_cmd('')
            '''Loose, Strict, Record, Timestamp, Verbose[none]'''
            result += self.exec_cmd('')
            '''Sweep range of sizes [n]'''
            result += self.exec_cmd('')
        else:
            result += self.exec_cmd('ping '+target)
        if '!!!' not in result:
            result += self.get_output(sleep_seconds=10)
        return result

# if __name__ == '__main__':
#     tc = TelnetClient()
#     tc.login('172.16.0.3', 'root', '123456')
#     tc.switch_root('123456')
#     tc.exec_cmd('show ip route')
#     tc.switch_normal()
#     tc.logout()