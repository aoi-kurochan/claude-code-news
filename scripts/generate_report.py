#!/usr/bin/env python3
"""
Claude Code 日次ニュースレポート生成スクリプト
Anthropic API の web_search ツールを使ってウェブ検索し、日本語レポートを生成する。
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import anthropic

JST = timezone(timedelta(hours=9))


def generate_report(today: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""今日の日付は {today} です。

Claude Codeに関する最新のニュース、活用事例、アップデート情報をウェブで検索してください。
以下のキーワードで複数回検索してください：
- "Claude Code 活用事例 {today[:7]}"
- "Claude Code news {today}"
- "Claude Code update 2026"
- "Claude Code tips"
- "Anthropic Claude Code {today[:7]}"
- "Claude Code 使い方"

収集した情報をもとに、以下の形式で日本語Markdownレポートを作成してください。
Markdownの内容だけを出力し、コードブロック（```）では囲まないでください。

# Claude Code ニュースレポート {today}

## 最新ニュース・アップデート

（最新のアップデート、リリース、Anthropicからの発表など）

## 活用事例・Tips

（実際の活用事例、便利なTips、ベストプラクティスなど）

## 注目の記事・リンク

（ソースURLをMarkdownリンクとして含めること）
"""

    messages = [{"role": "user", "content": prompt}]

    # web_search ツールを使って Claude に自律的に検索・レポート生成させる
    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            tools=[
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 10,
                }
            ],
            messages=messages,
        )

        # tool_use が含まれていれば続行
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": block.input.get("query", ""),
                        }
                    )
            messages.append({"role": "user", "content": tool_results})
            continue

        # end_turn になったらテキストを取り出して返す
        text_parts = [b.text for b in response.content if hasattr(b, "text")]
        return "\n".join(text_parts).strip()


def main():
    today = datetime.now(JST).strftime("%Y-%m-%d")
    print(f"Generating report for {today}...")

    report_content = generate_report(today)

    # reports/ ディレクトリに保存
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f"{today}.md"
    report_path.write_text(report_content, encoding="utf-8")

    print(f"Report saved: {report_path}")
    print(f"Content length: {len(report_content)} chars")


if __name__ == "__main__":
    main()
