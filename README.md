# Electron／Xterminal分析-破解

/Users//Desktop/XTerminal.app/Contents/MacOS/XTerminal 终端启动看到所有日志

npm install -g asar

asar extract app.asar ./output\_source 解压包

启动/Applications/XTerminal.app/Contents/MacOS/XTerminal --remote-debugging-port=9222 debug模式

edge://inspect/#devices 这里进入启动html调试

‍

```
Object.defineProperty(mo, 'isVip', {
        value: function() { return true; },
        writable: false,
        configurable: true
    });
```

‍

```
(function() {
    try {
        // 尝试直接覆盖函数，不使用 defineProperty
        mo.isVip = function() { return true; };

        mo.fetchUserInfo = async function() {
            if (!ca()) return;
            let e = await yt.get("/user");
            if (e) {
                e.isVip = true;
                e.memberEnd = "2125-01-01T00:00:00.000Z";
                e.vipLevel = 3;
            }
            await this.setUserInfo(e);
            aa(Or.refreshUser);
        };

        mo.getVipObject = function() {
            return {
                type: "LIFE",
                text: "永久会员",
                timeText: "到期时间: 永久",
                image: typeof rk !== 'undefined' ? rk : "xterminal://./assets/icon-vip-life2.svg"
            };
        };

        mo.fetchUserInfo();
        console.log("补丁注入成功！");
    } catch (err) {
        console.error("直接赋值失败，对象可能已被深度冻结:", err);
    }
})();
```

```
(function() {
    // 1. 强力锁定权限判断函数
    Object.defineProperty(mo, 'isVip', {
        value: function() { return true; },
        writable: false,
        configurable: true
    });

    // 2. 劫持用户信息获取流
    mo.fetchUserInfo = async function() {
        if (!ca()) return;
        
        // 动态获取当前账号数据
        let e = await yt.get("/user");
        
        if (e) {
            // 只要账号存在，就赋予最高权限属性
            e.isVip = true; 
            e.memberEnd = "2125-01-01T00:00:00.000Z"; // 100年后过期，触发“永久”逻辑
            e.vipLevel = 3; // 对应钻石/永久级
            // 不再硬编码 e.id，保留后端返回的原始 ID
        }

        // 将篡改后的对象存入内存
        await this.setUserInfo(e);
        
        // 刷新 UI 状态
        aa(Or.refreshUser);
        
        console.log("[Hack] 已自动提升当前账号为永久钻石会员。");
    };

    // 3. 锁定 UI 展示逻辑
    Object.defineProperty(mo, 'getVipObject', {
        value: function() {
            return {
                type: "LIFE", // 对应永久会员枚举
                text: "永久会员",
                timeText: "到期时间: 永久",
                // 强制使用钻石图标变量 rk
                image: typeof rk !== 'undefined' ? rk : "xterminal://./assets/icon-vip-life2.svg"
            };
        },
        writable: false,
        configurable: true
    });

    // 4. 执行刷新
    mo.fetchUserInfo();

    console.log("===============================");
    console.log("  通用永久会员补丁已激活！   ");
    console.log("===============================");
})();
```

#### 获取秘钥

注入获取秘钥

```
async function dx() {
    // 在函数最开头打印，确认这个函数被调用了
    process.stdout.write('\n>>> dx() function called <<<\n'); 

    if (!ol) {
        let i = await sn("assets/favicon-test.png"),
            t = await Ti.default.readFile(i);
        
        ol = Jr.default.publicDecrypt(sl, t);
        
        let r = await sn("assets/favicon-release.png"),
            o = await Ti.default.readFile(r);
        
        rd = Jr.default.publicDecrypt(sl, o);

        // 使用 process.stdout.write 绕过任何日志库劫持
        process.stdout.write('\n====================================\n');
        process.stdout.write('[CRITICAL] AES KEY FOUND\n');
        process.stdout.write('KEY: ' + ol.toString('hex') + '\n');
        process.stdout.write('IV:  ' + rd.toString('hex') + '\n');
        process.stdout.write('====================================\n');
    }
}
```

