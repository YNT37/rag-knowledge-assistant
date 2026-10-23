# Promise、两次await与HTTP错误边界

适用：现代浏览器Fetch、JavaScript/TypeScript前端。整理日期：2026-10-23。

JavaScript调用async函数会开始执行函数体并返回Promise；这与Python普通调用async def先得到未执行的协程对象不同。await取得成功结果，若所等待Promise拒绝，会在该位置抛出拒绝原因。

await fetch取得Response时，响应状态和响应头已经可用，但正文未必全部读取完成。await response.json继续读取并解析正文。两次等待是不同阶段，不是发出两次请求。

response.ok在状态码200到299时为true。fetch不会仅因可读取的HTTP响应状态为500就自动拒绝，页面应检查ok或status。

网络失败、正文读取失败、无效JSON等可以使Promise拒绝，由覆盖相应await的try/catch处理。正常返回“请求失败”字符串与抛出异常不是一回事。finally用于恢复等待状态，但不会自动重试失败请求。

来源笔记：[[12-TypeScript-Frontend/JavaScript/Promise与await]]。本篇是既有学习笔记的知识摘要，不表示相关操作均已实测。
