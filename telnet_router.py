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
            result += self.exec_cmd('ip address ' + secondary_ip['ip'] + ' ' + secondary_ip['netmask'] + 'secondary')
        result += self.exec_cmd('no shutdown')
        self.exec_cmd('exit')
        self.exec_cmd('exit')
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
        info['ip_address'] = {'primary':{}, 'secondary':[]}
        for str in output.split('\r\n'):
            if 'down' in str:
                info['is_open'] = False
                return info
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

# if __name__ == '__main__':
#     tc = TelnetClient()
#     tc.login('172.16.0.3', 'root', '123456')
#     tc.switch_root('123456')
#     tc.exec_cmd('show ip route')
#     tc.switch_normal()
#     tc.logout()