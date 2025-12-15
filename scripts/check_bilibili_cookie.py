#!/usr/bin/env python3
"""
检查B站Cookie配置脚本
用于验证环境变量是否正确配置
"""
import os
import sys

def check_cookie_config():
    """检查B站Cookie配置"""
    print("=" * 60)
    print("B站Cookie配置检查")
    print("=" * 60)
    print()
    
    # 检查各个环境变量
    cookies = {
        'BILI_SESSDATA': {
            'name': 'SESSDATA',
            'required': True,
            'description': '登录凭证（最重要）'
        },
        'BILI_JCT': {
            'name': 'bili_jct',
            'required': True,
            'description': 'CSRF token'
        },
        'BILI_BUVID3': {
            'name': 'buvid3',
            'required': False,
            'description': '设备标识（可选）'
        },
        'BILI_DEDEUSERID': {
            'name': 'DedeUserID',
            'required': False,
            'description': '用户ID（可选）'
        }
    }
    
    all_ok = True
    required_ok = True
    
    for env_var, info in cookies.items():
        value = os.getenv(env_var)
        if value:
            status = "✅"
            if info['required']:
                if len(value) < 10:
                    status = "⚠️"
                    print(f"{status} {env_var}: 已配置，但值太短（可能不正确）")
                    print(f"   值: {value[:20]}...")
                else:
                    print(f"{status} {env_var}: 已配置")
                    print(f"   值长度: {len(value)} 字符")
                    print(f"   值预览: {value[:30]}...")
            else:
                print(f"{status} {env_var}: 已配置（可选）")
                print(f"   值: {value}")
        else:
            status = "❌" if info['required'] else "⚠️"
            print(f"{status} {env_var}: 未配置")
            if info['required']:
                print(f"   ⚠️  这是必需的Cookie！")
                required_ok = False
            else:
                print(f"   （可选，但建议配置）")
            all_ok = False
        
        print(f"   说明: {info['description']}")
        print()
    
    # 检查备用Cookie
    bili_cookie = os.getenv("BILI_COOKIE")
    if bili_cookie:
        print(f"✅ BILI_COOKIE: 已配置（备用Cookie字符串）")
        print(f"   值长度: {len(bili_cookie)} 字符")
        print()
    
    # 总结
    print("=" * 60)
    if required_ok:
        print("✅ 必需的Cookie已配置完成！")
        print()
        print("下一步：")
        print("1. 重启服务器使配置生效")
        print("2. 查看服务器日志，应该看到：")
        print("   '已加载 B 站凭证，用于减轻 412 风控'")
        print("3. 测试API请求是否正常")
    else:
        print("❌ 缺少必需的Cookie配置！")
        print()
        print("请按照以下步骤配置：")
        print("1. 参考文档：docs/项目文档/04-功能说明/API集成/B站Cookie获取指南.md")
        print("2. 获取SESSDATA和bili_jct的值")
        print("3. 设置环境变量：")
        print("   export BILI_SESSDATA='你的SESSDATA值'")
        print("   export BILI_JCT='你的bili_jct值'")
        print("4. 或创建.env文件（推荐）")
    print("=" * 60)
    
    return required_ok

if __name__ == "__main__":
    try:
        # 尝试加载.env文件（如果存在）
        try:
            from dotenv import load_dotenv
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
                print(f"📄 已加载 .env 文件: {env_path}\n")
            else:
                print("ℹ️  未找到 .env 文件，使用系统环境变量\n")
        except ImportError:
            print("ℹ️  python-dotenv 未安装，仅使用系统环境变量\n")
            print("   提示：安装 python-dotenv 可以支持 .env 文件")
            print("   pip install python-dotenv\n")
        
        success = check_cookie_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 检查过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
