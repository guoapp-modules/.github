# 参与贡献

guoapp-modules 里每个仓库是 [guoapp](https://github.com/Xanerix/guoapp) 的一个站源模块。清单字段、导出函数和宿主接口见 guoapp 开发指南的[「站源模块」](https://github.com/Xanerix/guoapp/blob/main/DEVELOPMENT.md#站源模块)。

## 改进已有模块

fork 对应的模块仓库，改好后提 PR。CI 会校验清单格式、`main.js` 语法，并拒绝压缩或混淆过的代码（单行不超过 1000 个字符）。

- 不要改剧和分集 ID 的格式，它们已经写进用户的追剧、观看记录和下载。
- 只请求清单 `hosts` 里的域名；新增域名要在 PR 里说明用途。
- 不用改 `version`，发版由维护者负责。

## 新增模块

1. 用 [template](https://github.com/guoapp-modules/template) 在自己的账号下新建仓库，仓库名就是模块标识。
2. 按模板说明写好模块，改 `version` 并打 `v<版本号>` 标签推送，CI 会发布 Release。
3. 要上架应用内的模块商店（我的 › 模块 › 在线仓库），就在 [index](https://github.com/guoapp-modules/index) 开 issue 申请。审核通过后，仓库会转进 guoapp-modules 组织再上架，流程和要求见那里的说明。未上架的模块也可以用 Release 里的 zip 手动安装。

转入组织后，你仍是仓库的协作者，提交记录照旧保留。之后的改动和改进已有模块一样，从你的 fork 提 PR，维护者合并后发版。

## 宿主接口

模块需要宿主提供新的接口或能力时，请向 [guoapp](https://github.com/Xanerix/guoapp) 提 issue 或 PR。
