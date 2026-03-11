# astrbot_plugin_qqfarm

QQ农场助手插件，通过指令管理 QQ 农场账号。

**功能**
- 查看账号状态与详情
- 更新账号 Code
- 启动/停止账号

**安装**
1. 将本仓库放入 AstrBot 的插件目录（通常为 `data/plugins/`）
2. 在 AstrBot 运行环境中安装依赖：

```bash
pip install -r requirements.txt
```

3. 重载/重启 AstrBot

**配置**
插件使用 `_conf_schema.json` 定义配置项，请在 AstrBot 的插件配置页面填写：
- `base_url`：QQ Farm Bot UI 服务地址（必填）
- `token`：x-admin-token（可选）
- `admin_password`：管理员密码（可选，用于登录获取新 token）

**指令**
- `农场状态`：查看所有账号状态
- `农场详情 [账号ID]`：查看指定账号详情
- `更新农场Code [账号ID] [Code]`：更新账号 Code
- `启动农场 [账号ID]`：启动账号
- `停止农场 [账号ID]`：停止账号
- `农场帮助`：查看帮助

**注意**
- 未配置 `base_url` 时插件会提示配置后再使用
- token 与管理员密码至少填写其一
