# 有声书生成工具

本项目提供了一个基本的工具，用于将文本生成有声书。它利用大型语言模型（LLM）进行角色和音色分配，并使用文本转语音（TTS）服务进行音频合成。本项目包含图形用户界面（GUI）和简单的API接口。

## 功能

*   **文本转有声书：** 将输入的文本文件转换为多角色MP3有声书。
*   **LLM 集成：** 使用LLM识别文本中的说话者并分配合适的音色。
*   **TTS 集成：** 使用第三方TTS服务合成语音。
*   **角色音色管理：** 存储和重用音色分配，以保持角色声音的一致性。
*   **GUI：** 一个简单的桌面应用程序，用于交互式操作。
*   **API：** 一个基本的Web API，用于程序化访问。

## 设置

1.  **克隆仓库：**
    ```bash
    git clone [repository_url]
    cd audiobook_generator
    ```
    （假设用户会将此项目放入git仓库中）
2.  **安装依赖：**
    ```bash
    pip install -r requirements.txt
    ```
3.  **配置API凭据：**
    在项目根目录创建 `.env` 文件，并填入您的API凭据。已提供模板：
    ```
    # 有声书生成工具的API凭据
    # 请替换为您的实际API密钥和端点

    LLM_ENDPOINT=https://ark.cn-beijing.volces.com/api/v3/chat/completions
    LLM_API_KEY=YOUR_LLM_API_KEY
    LLM_MODEL_NAME=doubao-seed-1-6-250615

    TTS_APP_ID=YOUR_TTS_APP_ID
    TTS_ACCESS_KEY=YOUR_TTS_ACCESS_KEY
    TTS_RESOURCE_ID=volc.service_type.10029
    ```
    *   `YOUR_LLM_API_KEY`：您的LLM服务API密钥。
    *   `LLM_MODEL_NAME`：（可选）LLM的具体模型名称。默认为 `doubao-seed-1-6-250615`。
    *   `YOUR_TTS_APP_ID`：您的TTS服务App ID。
    *   `YOUR_TTS_ACCESS_KEY`：您的TTS服务Access Key。
    *   `YOUR_TTS_RESOURCE_ID`：您的TTS服务Resource ID。

## 使用方法

### GUI 应用程序

运行GUI：
```bash
python -m src.main
```
GUI允许您选择输入文本文件，配置API凭据，并生成有声书。

### Web API

运行API：
```bash
python -m src.main api
```
API将在 `http://127.0.0.1:5000` 启动。

**API 端点：**

*   **POST /generate_audiobook**
    *   **描述：** 触发从提供的文本生成有声书。
    *   **请求体 (JSON)：**
        ```json
        {
            "text": "您的书籍章节或段落内容。",
            "project_id": "项目唯一标识符"
        }
        ```
        *   `text`：（必填）要转换为语音的文本内容。
        *   `project_id`：（可选）此生成任务的唯一标识符。如果未提供，将生成一个随机标识符。
    *   **响应 (JSON)：**
        ```json
        {
            "task_id": "任务唯一ID",
            "status_url": "/status/任务唯一ID"
        }
        ```
        *   `task_id`：异步生成任务的唯一ID。
        *   `status_url`：用于检查任务状态的URL。

*   **GET /status/<task_id>**
    *   **描述：** 获取有声书生成任务的当前状态。
    *   **响应 (JSON)：**
        ```json
        {n            "status": "queued" | "processing" | "completed" | "failed",
            "progress": "当前进度信息",
            "file_path": "/path/to/generated/audiobook.mp3", // 仅当状态为 'completed' 时
            "download_url": "/download/generated_audiobook.mp3" // 仅当状态为 'completed' 时
        }
        ```

*   **GET /download/<filename>**
    *   **描述：** 下载生成的有声书文件。
    *   **参数：**
        *   `filename`：要下载的有声书文件名（例如，`final_audiobook_your_project_id.mp3`）。

## 注意事项

*   这是一个基本实现。对于生产环境使用，请考虑更健壮的错误处理、异步任务管理（例如 Celery）和安全的凭据管理。
*   确保您的API凭据具有LLM和TTS服务所需的权限。
*   网络连接和代理设置可能会影响API访问。
