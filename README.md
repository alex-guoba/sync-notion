<p align="center">
  <img alt="Example Page" src="https://github.com/alex-guoba/sync-notion/assets/2872637/4bcb0692-8881-4f39-abce-22495c8a3fcc" width="689">
</p>

# 将微信读书笔记、github trending、memos 自动同步到 Notion

本项目支持将微信读书笔记（划线及评论）、github trending 同步 Notion。支持本地手工、github action 定期两种方式。可以修改 action 配置自行按需选择。

[English](./README.md) | 简体中文

## Requirements

Python 3.10

## 同步微信读书笔记

### 使用

1. star 本项目

2. fork 这个工程，删除目录中的临时存储文件(./var/sync_read.db)

3. 获取微信读书的 Cookie: `WEREAD_COOKIE`

- 浏览器打开 https://weread.qq.com/
- 微信扫码登录确认，提示没有权限忽略即可
- 按 F12 进入开发者模式，依次点 Network -> Doc -> Headers-> cookie。复制 Cookie 字符串;

4. 获取 NotionToken: `NOTION_TOKEN`

- 浏览器打开https://www.notion.so/my-integrations
- 点击 New integration 输入 name 提交
- 点击 show，然后 copy

5. 复制[这个 Notion 模板](https://gelco.notion.site/67639069c7b84f55b6394f16ecda0c4f?v=b5d09dc635db4b3d8ba13b200b88d823&pvs=25)，删掉所有的数据，并点击右上角设置，Connections 添加你创建的 Integration。

6. 获取 NotionDatabaseID: `NOTION_DATABASE_ID`

- 打开 Notion 数据库，点击右上角的 Share，然后点击 Copy link
- 获取链接后比如https://gelco.notion.site/67639069c7b84f55b6394f16ecda0c4f?v=b5d09dc635db4b3d8ba13b200b88d823&pvs=25 中间的**67639069c7b84f55b6394f16ecda0c4f**就是 DatabaseID

7. 同步方式

- **方式一**：在 Github 的 Secrets 中添加以下变量来实现每日自动同步

  - 打开你 fork 的工程，点击 Settings->Secrets and variables->New repository secret
  - 添加以下变量(**变量名称自定义，只要与 action 中对应的名称一致即可**)
    - `WEREAD_COOKIE`
    - `NOTION_TOKEN`
    - `NOTION_DATABASE_ID`

- **方式二**： 也可以本地运行脚本完成同步:

```shell
pip install -r requirements.txt
python3 ./main.py sync_read ${WEREAD_COOKIE} ${NOTION_TOKEN} ${NOTION_DATABASE_ID}
```

### 高级特性

1. 可以配合 [next-blogger](https://github.com/alex-guoba/next-blogger) 搭建自己的**读书笔记分享**网站。样式参考 [goroutine.cn](https://goroutine.cn/notes)

2. 【可选】可以指定单独的 Notion 数据库，用于存储每日同步记录，用作 calender 视图等场景。

- action 中环境变量`NOTION_DATABASE_CALENDAR`，命令行方式参考[action](./.github/workflows/weread.yml)。模板参考[这个](https://gelco.notion.site/5a17a1f794464652ade156c4c7572736?v=d961ee4d64864620b948b1a18fb1ebdd&pvs=4)

- 注意：也需要在 Connections 添加你创建的 Integration。流程与上面一致。

3. 支持[Server 酱](https://sct.ftqq.com/)微信通知，用于在同步完成时发送微信通知更新读书笔记数。

- action 中环境变量`SCKEY`，参考[action](./.github/workflows/weread.yml)。申请方式参考[Server 酱](https://sct.ftqq.com/sendkey)。

### 增量同步说明

#### 更新时机

1. 微信读书笔记为增量同步，每次同步时，会根据笔记的更新时间进行筛选。仅当微信读书中书籍有**笔记更新**时才会触发同步。
2. 可以删除 db 中已同步过的书籍页面(page)，删除后下次同步时会全同步（注意需要在微信读书中触发一次笔记更新，比如新增、删除任意笔记即可）。

#### 增量机制

1. 已同步到 Notion 的笔记，用户可以在 Notion 中**新增、修改**笔记内容，下次同步时，**不会覆盖已同步过的笔记**。
2. 增量笔记同步顺序：新增章节会按照微信读书的章节顺序插入；新增笔记会插入到对应的章节下，但不保证同一章节下的笔记与微信读书一致。
3. 用户可以在 database 中新增字段，用做书籍的自定义标识。但不得修改已有字段。
4. 已同步到 Notion 的笔记，**用户不得删除章节信息**，否则下次同步同一章节的增量笔记无法精确定位。

### 原理说明

Notion 无法保存微信读书的笔记 id 等信息，所以在仓库中存储了一份微信读书笔记 ID 与[Notion Block ID](https://developers.notion.com/reference/patch-block-children)的映射关系。每次更新完毕后在 git action 中自动提交到仓库。
所以如果用户 clone 了本仓库到，首次运行时可以先删除原仓库中的映射文件(./var/sync_read.db)。

### 支持的配置项

```ini
[weread.format]
ContentType = list
EnableEmoj = false
EnableReadingDetail = true
```

- ContentType：增加笔记内容 block 组织形式配置，可以将内容展现形态指定为 paragraph/list/callout。
- EnableEmoj：开启、禁用 emoj
- EnableReadingDetail: 开启、禁用阅读明细。

## 同步 Github Trending

### 使用

与微信读书同步方法基本一致。

1. 获取 NotionToken（可复用）

2. 创建 NotionDatabase，获取 NotionDatabaseID， notion 模板参考[这个](https://gelco.notion.site/77a3c6c8c2fb405e8347a7bde96d51d1?v=5c6464969afa432ea473f07c7b6959e8)

3. 本地运行方式

```shell
pip install -r requirements.txt
python3 ./main.py sync_trending ${NOTION_TOKEN} ${NOTION_DATABASE_TRENDING} --git_token=${GIT_TOKEN}
```

4. 或者在 Github 的 Secrets 中添加以下变量来实现每日自动同步

- 打开你 fork 的工程，点击 Settings->Secrets and variables->New repository secret
- 添加以下变量 (**变量名称自定义，只要与 action 中对应的名称一致即可**)
  - NOTION_TOKEN
  - NOTION_DATABASE_TRENDING
  - GIT_TOKEN
    如果不需要仓库的其他信息（包括 fork、star、watcher 数量），GIT_TOKEN 可以不配置

### 支持的配置项

```ini
[trending.language]
languages = python,go
```

- languages: 关注的项目语言，不允许为空

## 同步 ProductHunt 产品列表到 Notion

### 使用

与微信读书同步方法基本一致。产品列表参考[ProductHunt](https://www.producthunt.com/all)

1. 获取 NotionToken（可复用）

2. 创建 NotionDatabase，获取 NotionDatabaseID， notion 模板参考[这个](https://gelco.notion.site/1467b35a24cd80449eeadf5ed024cef5?v=1a470daa9fc0418d8682aaf789860d40&pvs=73)
3. 本地运行

```shell
python3 ./main.py sync_producthunt ${NOTION_TOKEN} ${DATABASE_ID}
```

```ini
[producthunt.filter]
; 过滤条件，可选
MinVotes = 5
MinComments = 5
```

也可配置 github action 来实现定期同步，有需要修改 github action 以及配置对应环境即可。

```shell
# git中配置好对应的环境变量，设置对应的action run指令即可
python3 ./main.py sync_producthunt "${{secrets.NOTION_TOKEN}}" "${{DATABASE_ID_PH}}"
```

## 感谢

- [malinkang / weread_to_notion](https://github.com/malinkang/weread_to_notion)
- [bonfy / github-trending](https://github.com/bonfy/github-trending)
