#!/usr/bin/env python3
"""
火山引擎音视频字幕生成 API 客户端
使用纯 Python 3 标准库，无第三方依赖

Usage:
    python3 volc_asr.py <audio_file> [--appid XXX] [--token XXX] [--language zh-CN] [--timeout 600]

Environment:
    VOLC_ASR_APPID    - 应用 ID
    VOLC_ASR_TOKEN    - 访问令牌

Output (stdout):
    JSON 格式：
    {
        "segments": [{"start": 0.0, "end": 3.197, "text": "识别文本"}, ...],
        "full_text": "完整文本",
        "duration": 5.3,
        "source": "volc_asr"
    }
"""

import sys
import os
import json
import time
import argparse
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError


# API 常量
SUBMIT_URL = "https://openspeech.bytedance.com/api/v1/vc/submit"
QUERY_URL = "https://openspeech.bytedance.com/api/v1/vc/query"


def log(msg):
    """输出到 stderr，不影响 stdout 的 JSON 输出"""
    print(msg, file=sys.stderr, flush=True)


def submit_audio(audio_path, appid, token, language="zh-CN"):
    """
    提交音频文件到火山引擎 ASR

    Returns:
        task_id (str): 任务 ID
    """
    log(f"Reading audio file: {audio_path}")

    # 读取音频文件
    with open(audio_path, 'rb') as f:
        audio_data = f.read()

    file_size_mb = len(audio_data) / (1024 * 1024)
    log(f"Audio file size: {file_size_mb:.2f} MB")

    # 检测文件类型
    if audio_path.lower().endswith('.mp3'):
        content_type = 'audio/mp3'
    elif audio_path.lower().endswith('.wav'):
        content_type = 'audio/wav'
    else:
        content_type = 'audio/wav'  # 默认

    # 构建 URL 参数
    params = {
        'appid': appid,
        'language': language,
        'use_itn': 'True',
        'use_punc': 'True',
        'words_per_line': '100',
        'max_lines': '1'
    }
    url = f"{SUBMIT_URL}?{urlencode(params)}"

    # 构建请求
    log("Submitting to Volcengine ASR...")
    headers = {
        'Authorization': f'Bearer; {token}',
        'Content-Type': content_type
    }

    req = Request(url, data=audio_data, headers=headers, method='POST')

    try:
        with urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        log(f"HTTP Error {e.code}: {error_body}")
        raise RuntimeError(f"Submit failed: HTTP {e.code}")
    except URLError as e:
        log(f"Network error: {e.reason}")
        raise RuntimeError(f"Submit failed: {e.reason}")

    # 检查响应
    if result.get('code') != 0:
        raise RuntimeError(f"Submit failed: {result.get('message', 'Unknown error')}")

    task_id = result.get('id')
    if not task_id:
        raise RuntimeError("No task ID in response")

    log(f"Task submitted: {task_id}")
    return task_id


def query_result(task_id, appid, token, timeout=600):
    """
    查询转录结果（阻塞等待）

    Returns:
        dict: 包含 segments, full_text, duration 的字典
    """
    params = {
        'appid': appid,
        'id': task_id,
        'blocking': '1'  # 阻塞等待
    }
    url = f"{QUERY_URL}?{urlencode(params)}"

    headers = {
        'Authorization': f'Bearer; {token}'
    }

    log(f"Querying result (blocking, timeout={timeout}s)...")
    start_time = time.time()

    req = Request(url, headers=headers)

    try:
        with urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        log(f"HTTP Error {e.code}: {error_body}")
        raise RuntimeError(f"Query failed: HTTP {e.code}")
    except URLError as e:
        log(f"Network error: {e.reason}")
        raise RuntimeError(f"Query failed: {e.reason}")

    elapsed = time.time() - start_time
    log(f"Query completed in {elapsed:.1f}s")

    # 检查响应
    if result.get('code') != 0:
        raise RuntimeError(f"Query failed: {result.get('message', 'Unknown error')}")

    # 解析结果
    utterances = result.get('utterances', [])
    duration = result.get('duration', 0)

    # 转换为 whisper 兼容格式（毫秒 -> 秒）
    segments = []
    for utt in utterances:
        segments.append({
            'start': round(utt['start_time'] / 1000.0, 3),  # 毫秒转秒
            'end': round(utt['end_time'] / 1000.0, 3),
            'text': utt['text'].strip()
        })

    full_text = ' '.join(seg['text'] for seg in segments)

    log(f"Transcription complete: {len(segments)} segments, {len(full_text)} chars, {duration}s audio")

    return {
        'segments': segments,
        'full_text': full_text,
        'duration': duration,
        'source': 'volc_asr'
    }


def main():
    parser = argparse.ArgumentParser(
        description='火山引擎音视频字幕生成 API 客户端',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('audio_file', help='音频文件路径 (mp3/wav)')
    parser.add_argument('--appid', default=os.getenv('VOLC_ASR_APPID'), help='应用 ID (或使用环境变量 VOLC_ASR_APPID)')
    parser.add_argument('--token', default=os.getenv('VOLC_ASR_TOKEN'), help='访问令牌 (或使用环境变量 VOLC_ASR_TOKEN)')
    parser.add_argument('--language', default='zh-CN', help='语言代码 (默认: zh-CN)')
    parser.add_argument('--timeout', type=int, default=600, help='查询超时时间(秒) (默认: 600)')

    args = parser.parse_args()

    # 检查必需参数
    if not args.appid:
        log("Error: --appid is required (or set VOLC_ASR_APPID)")
        sys.exit(1)

    if not args.token:
        log("Error: --token is required (or set VOLC_ASR_TOKEN)")
        sys.exit(1)

    if not os.path.isfile(args.audio_file):
        log(f"Error: Audio file not found: {args.audio_file}")
        sys.exit(1)

    try:
        # 提交音频
        task_id = submit_audio(args.audio_file, args.appid, args.token, args.language)

        # 查询结果
        result = query_result(task_id, args.appid, args.token, args.timeout)

        # 输出 JSON 到 stdout
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)

    except KeyboardInterrupt:
        log("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        log(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
