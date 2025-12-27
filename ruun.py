import os
import re
import shutil
import subprocess
import sys
import platform
import ctypes
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad

print("请运行: npm install -g @electron/asar和 pip install pycryptodome")


# ================= 配置区 =================

def get_app_root():
    """
    获取软件资源路径
    优先使用当前目录(支持安装在D盘的情况)，其次查找系统默认路径
    """
    cwd = os.getcwd()
    # 1. 如果当前目录下就有 app.asar 或 app 文件夹，直接用当前目录
    if os.path.exists(os.path.join(cwd, "app.asar")) or os.path.exists(os.path.join(cwd, "app")):
        return cwd

    system_name = platform.system()
    if system_name == "Windows":
        # 检测常见安装位置
        candidates = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'XTerminal', 'resources'),
            os.path.join(os.environ.get('ProgramFiles', ''), 'XTerminal', 'resources'),
            os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'XTerminal', 'resources')
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[0]  # 默认回退
    elif system_name == "Darwin":
        return "/Applications/XTerminal.app/Contents/Resources"
    else:
        # Linux 或其他，假设在当前目录
        return cwd


APP_ROOT = get_app_root()
APP_ASAR = os.path.join(APP_ROOT, "app.asar")
APP_UNPACKED = os.path.join(APP_ROOT, "app")
# 默认搜索路径
SEARCH_DIR = os.path.join(APP_ASAR, "dist", "render", "assets")

# 秘钥
AES_KEY_HEX = "7845687334447a4b5948334b5a3247464e6461547944796348636868386a5177"
AES_IV_HEX = "77516a3868686348637944795461644e"


# ================= 核心功能 =================

def is_admin():
    """ 跨平台检查管理员权限 """
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except:
        return False


def run_cmd(cmd):
    """ 执行 Shell 命令 """
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        print(f"❌ 命令执行失败: {cmd}")
        pass


def decrypt_content(hex_str):
    try:
        key = bytes.fromhex(AES_KEY_HEX)
        iv = bytes.fromhex(AES_IV_HEX)
        encrypted_data = bytes.fromhex(hex_str.strip())
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(encrypted_data)
        try:
            return unpad(decrypted, AES.block_size).decode('utf-8')
        except:
            return decrypted.decode('utf-8', errors='ignore').rstrip('\x00-\x1f')
    except:
        return None


def encrypt_content(text):
    key = bytes.fromhex(AES_KEY_HEX)
    iv = bytes.fromhex(AES_IV_HEX)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(text.encode('utf-8'), AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    return encrypted.hex()


def patch_vip_logic(content, filename):
    """ 修改逻辑 """
    modified = False

    # 1. 破解 isVip
    if "isVip()" in content:
        # 尝试正则
        new_content = re.sub(r'isVip\s*\(\)\s*\{[^}]*\}', 'isVip(){return true}', content)
        # 兼容性替换
        if new_content == content:
            new_content = content.replace("isVip(){", "isVip(){return true;")

        if new_content != content:
            print(f"   [+] 检测到 isVip 校验")
            content = new_content
            modified = True

    # 2. 注入数据劫持 (setUserInfo)
    if "async setUserInfo(e)" in content:
        hook_code = 'async setUserInfo(e){if(e){e.isVip=true;e.vipLevel=3;e.memberEnd="2125-01-01T00:00:00.000Z";}'
        if 'e.memberEnd="2125' not in content:
            new_content = content.replace('async setUserInfo(e){', hook_code)
            if new_content != content:
                print(f"   [+] 检测到 setUserInfo 数据层")
                content = new_content
                modified = True

    return content, modified


def main():
    # === 修复点：Global 声明必须放在函数第一行 ===
    global APP_ASAR, SEARCH_DIR

    # 权限检查
    if not is_admin():
        print("❌ 权限不足！")
        if platform.system() == "Windows":
            print("⚠️  请右键点击 CMD/PowerShell 选择【以管理员身份运行】")
        else:
            print("请使用 sudo 运行")
        sys.exit(1)

    print(f"🚀 开始执行 (系统: {platform.system()})...")
    print(f"📂 目标路径: {APP_ROOT}")

    if not os.path.exists(APP_ROOT):
        print("❌ 找不到目录，请确认你在 resources 目录下运行，或软件已安装。")
        return

    # 1. 自动处理 asar
    os.chdir(APP_ROOT)

    if os.path.isfile(APP_ASAR):
        print("📦 正在解包 app.asar ...")

        if shutil.which('asar') is None:
            print("❌ 未找到 asar 命令。")
            print("   Windows 请运行: npm install -g @electron/asar和 pip install pycryptodome")
            return

        # Windows 下解包
        run_cmd(f"asar extract app.asar app")

        if os.path.exists("app"):
            print("   解包成功，移除原文件并重命名...")
            try:
                os.remove("app.asar")  # 删除原文件
                os.rename("app", "app.asar")  # 重命名文件夹
                print("✅ 已转换为文件夹模式")
            except Exception as e:
                print(f"❌ 文件操作失败(占用中?): {e}")
                print("   请先完全关闭 XTerminal (检查托盘图标)")
                return
        else:
            print("❌ 解包失败，未生成 app 目录")
            return

    elif os.path.isdir(APP_ASAR):
        print("ℹ️  已是文件夹模式，直接开始扫描")
    else:
        # 兼容逻辑：如果没有 app.asar 但有 app 文件夹
        if os.path.isdir(APP_UNPACKED):
            print("ℹ️  发现 app 文件夹 (非 asar 后缀)，修正路径...")
            APP_ASAR = APP_UNPACKED
            SEARCH_DIR = os.path.join(APP_ASAR, "dist", "render", "assets")
        else:
            print("❌ 找不到 app.asar 或 app 文件夹")
            return

    # 2. 遍历解密并替换
    print(f"📂 扫描资源: {SEARCH_DIR}")
    count = 0

    if not os.path.exists(SEARCH_DIR):
        print(f"❌ 资源目录不存在: {SEARCH_DIR}")
        return

    for root, dirs, files in os.walk(SEARCH_DIR):
        for file in files:
            if file.endswith(".js"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        hex_content = f.read()

                    clear_text = decrypt_content(hex_content)

                    if clear_text and ("isVip" in clear_text or "setUserInfo" in clear_text):
                        new_text, is_modified = patch_vip_logic(clear_text, file)

                        if is_modified:
                            print(f"   -> 修改并写入: {file}")
                            encrypted_hex = encrypt_content(new_text)
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(encrypted_hex)
                            count += 1
                except Exception:
                    pass

    # 3. 清理工作
    print("\n🧹 执行清理...")

    update_yml = os.path.join(APP_ROOT, "app-update.yml")
    if os.path.exists(update_yml):
        try:
            os.remove(update_yml)
            print("   [+] 已删除 app-update.yml")
        except:
            pass

    # 删除缓存
    cache_path = ""
    if platform.system() == "Windows":
        app_data = os.environ.get('APPDATA')
        if app_data:
            cache_path = os.path.join(app_data, "xterminal", ".cacheJs")
    else:
        cache_path = os.path.expanduser("~/Library/Application Support/xterminal/.cacheJs")

    if cache_path and os.path.exists(cache_path):
        try:
            shutil.rmtree(cache_path)
            print(f"   [+] 缓存已清理: {cache_path}")
        except Exception as e:
            print(f"   [!] 缓存清理失败: {e}")
    else:
        print("   [i] 未发现缓存文件")

    print("\n✅ 全部完成！请重启软件。")


if __name__ == "__main__":
    main()
