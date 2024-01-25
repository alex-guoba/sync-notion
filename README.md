#  Syncing Wechat Book Notes, Github Trending, Memos to Notion automatically

This project supports the synchronization of WeChat book notes, GitHub trending, and memos to Notion. It can be done locally or through regular GitHub actions, which can be customized according to your preferences.

English | [简体中文](./README.zh-CN.md)

## Requirements

Python 3.10

## Synchronizing WeChat Book Notes

### Usage

1. Star this project.
2. Fork this repository.
3. Obtain the WeChat book's Cookie.
	* Open <https://weread.qq.com/> in your browser.
	* Scan the QR code with WeChat and confirm login. Ignore any permission errors.
	* Press F12 to enter developer mode, then follow Network -> Doc -> Headers-> cookie. Copy the Cookie string.
4. Get the Notion Token.
	* Open <https://www.notion.so/my-integrations> in your browser.
	* Click "New integration" and enter a name to submit.
	* Click "show" and then copy the token.
5. Copy [this Notion template](https://gelco.notion.site/67639069c7b84f55b6394f16ecda0c4f?v=b5d09dc635db4b3d8ba13b200b88d823&pvs=25), delete all the data, and click the settings button in the top right corner. Add the integration you created under Connections.
6. Get the Notion Database ID.
	* Open the Notion database, click the "Share" button in the top right corner, and then click "Copy link".
	* The link will look like this: <https://gelco.notion.site/67639069c7b84f55b6394f16ecda0c4f?v=b5d09dc635db4b3d8ba13b200b88d823&pvs=25>. The **67639069c7b84f55b6394f16ecda0c4f** part is the Database ID.
7. Add the following variables to your GitHub Secrets to enable daily automatic synchronization:
	* Open your forked repository, click Settings -> Secrets and variables -> New repository secret.
	* Add the following variables (you can customize the variable names as long as they match the names in the action):
		+ WEREAD_COOKIE
		+ NOTION_TOKEN
		+ NOTION_DATABASE_ID
8. Alternatively, you can run the script locally:
```shell
pip install -r requirements.txt
python3 ./main.py sync_weread ${WEREAD_COOKIE} ${NOTION_TOKEN} ${NOTION_DATABASE_ID}
```

### Supported Configuration Options

```ini
[weread.format]
ContentType = list
EnableEmoj = false
EnableReadingDetail = true
```

* ContentType: Specifies the organization format of the note content blocks as paragraph/list/callout.
* EnableEmoj: Disables emojis.
* EnableReadingDetail: Add reading detail info to notes

## Synchronizing GitHub Trending

### Usage

The process is similar to synchronizing WeChat book notes.

1. Get the Notion Token (can be reused).
2. Create a Notion Database and get the Notion Database ID. Use this [template](https://gelco.notion.site/77a3c6c8c2fb405e8347a7bde96d51d1?v=5c6464969afa432ea473f07c7b6959e8) for reference.
3. To run locally:
```shell
pip install -r requirements.txt
python3 ./main.py sync_trending ${NOTION_TOKEN} ${NOTION_DATABASE_TRENDING} --git_token=${GIT_TOKEN}
```
4. Or add the following variables to your GitHub Secrets for daily automatic synchronization:
	* Open your forked repository, click Settings -> Secrets and variables -> New repository secret.
	* Add the following variables (you can customize the variable names as long as they match the names in the action):
		+ NOTION_TOKEN
		+ NOTION_DATABASE_TRENDING
		+ GIT_TOKEN (optional if you don't need repository information such as forks, stars, and watchers)

### Supported Configuration Options

```ini
[trending.language]
languages = python,go
```

* languages: The programming languages of the repositories to follow. This field cannot be empty.

## Syncing Memos to Notion

### Usage

The process is similar to syncing WeChat book notes.

1. Obtain a Notion Token (can be reused)
2. Create a Notion Database and get its ID. The Notion template can be referenced from [here](https://gelco.notion.site/b840c05d92af44719ee3d9d7f73010f8?v=f0a726764fa3455b9a28f50783eea58a&pvs=4)
3. Assign a unique [Token](https://usememos.com/docs/access-tokens) to the user on the Memos platform for accessing Memos.
4. Modify the configuration file to set the Memos host address and the user's UserName for pulling data. Note that the Token assigned to the user must match the UserName to access Private memos.
5. Run locally with the following command:
```shell
python3 ./main.py sync_memos ${NOTION_TOKEN} ${DATABASE_ID} ${MEMOS_TOKEN}
```

```ini
[memos.opts]
MemosHost = http://127.0.0.1:8081
; Username, not nickname
MemosUserName = memos-demo
```

It is also possible to configure GitHub Actions for regular syncing by modifying the action and configuring the corresponding environment variables.

```shell
# Configure the corresponding environment variables in git and set the action run command
python3 ./main.py sync_memos "${{secrets.NOTION_TOKEN}}" "${{DATABASE_ID}}" "${{MEMOS_TOKEN}}"
```

## Acknowledgments
- [malinkang / weread_to_notion](https://github.com/malinkang/weread_to_notion)
- [bonfy / github-trending](https://github.com/bonfy/github-trending)
- [usememos / memos](https://github.com/usememos/memos)
