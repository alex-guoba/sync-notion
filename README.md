# 将微信读书、github trending同步到Notion

本项目支持将微信读书笔记（划线及评论）、github trending到Notion。支持本地手工、github action定期两种方式。可以修改action配置自行按需选择。

### 同步微信读书笔记

#### 使用

1. star本项目

2. fork这个工程

3. 获取微信读书的Cookie

   * 浏览器打开 https://weread.qq.com/
   * 微信扫码登录确认，提示没有权限忽略即可
   * 按F12进入开发者模式，依次点 Network -> Doc -> Headers-> cookie。复制 Cookie 字符串;

4. 获取NotionToken

   * 浏览器打开https://www.notion.so/my-integrations
   * 点击New integration 输入name提交
   * 点击show，然后copy

5. 复制[这个Notion模板](https://gelco.notion.site/67639069c7b84f55b6394f16ecda0c4f?v=b5d09dc635db4b3d8ba13b200b88d823&pvs=25)，删掉所有的数据，并点击右上角设置，Connections添加你创建的Integration。

6. 获取NotionDatabaseID

   * 打开Notion数据库，点击右上角的Share，然后点击Copy link
   * 获取链接后比如https://gelco.notion.site/67639069c7b84f55b6394f16ecda0c4f?v=b5d09dc635db4b3d8ba13b200b88d823&pvs=25 中间的67639069c7b84f55b6394f16ecda0c4f就是DatabaseID

7. 在Github的Secrets中添加以下变量来实现每日自动同步

   * 打开你fork的工程，点击Settings->Secrets and variables->New repository secret
   * 添加以下变量
     * WEREAD_COOKIE
     * NOTION_TOKEN
     * NOTION_DATABASE_ID

8. 也可以本地运行脚本: 

   ```shell
   pip install -r requirements.txt
   python3 ./main.py sync_weread 
   ```

#### 支持的配置项

```ini
[weread.format]
ContentType = list
EnableEmoj = false
```

- ContentType：增加笔记内容block组织形式配置，可以将内容展现形态指定为paragraph/list/callout。
- EnableEmoj：禁用emoj



### 同步Github Trending

#### 使用

与微信读书同步方法基本一致。

1. 获取NotionToken（可复用）

2. 创建NotionDatabase，获取NotionDatabaseID， notion模板参考[这个](https://gelco.notion.site/77a3c6c8c2fb405e8347a7bde96d51d1?v=5c6464969afa432ea473f07c7b6959e8)

3. 本地运行

```shell
python3 ./main.py sync_trending
```

4. 或者在Github的Secrets中添加以下变量来实现每日自动同步

* 打开你fork的工程，点击Settings->Secrets and variables->New repository secret
* 添加以下变量
  * NOTION_TOKEN
  * NOTION_DATABASE_TRENDING
  * GIT_TOKEN
如果不需要仓库的其他信息（包括fork、star、watcher数量），GIT_TOKEN可以不配置

#### 支持的配置项

```ini
[trending.language]
languages = python,go
```

- languages: 关注的项目语言，不允许为空


### 同步Memos发表到Notion

#### 使用

与微信读书同步方法基本一致。

1. 获取NotionToken（可复用）

2. 创建NotionDatabase，获取NotionDatabaseID， notion模板参考[这个](https://gelco.notion.site/b840c05d92af44719ee3d9d7f73010f8?v=f0a726764fa3455b9a28f50783eea58a&pvs=4)

3. 在Memos平台为用户分配一个独立的Token供访问Memos使用。
   
4. 配置文件，设置memos host地址以及拉取人UserName。注意分配Token的用户身份与拉取人UserName一致才可以拉取到Private memo。

```ini
[memos.opts]
MemosHost = http://127.0.0.1:8081
MemosUserName = memos-demo
```

也可配置github action来实现定期同步，有需要修改github action即可。

```shell
python3 ./main.py sync_memos NOTION_TOKEN DATABASE_ID MEMOS_TOKEN
```


## 感谢

- [weread_to_notion](https://github.com/malinkang/weread_to_notion)
- [github-trending](https://github.com/bonfy/github-trending)