#!/usr/bin/env python3
"""
ES診断ツール - ローカル実行スクリプト

使い方:
    python run.py

オプション:
    --host: ホストアドレス（デフォルト: 0.0.0.0）
    --port: ポート番号（デフォルト: 8000）
    --reload: 自動リロード有効化（開発時用）
"""

import uvicorn
import argparse
import os
import sys

# srcディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    parser = argparse.ArgumentParser(description='ES診断ツール - FastAPIサーバー')
    parser.add_argument('--host', default='0.0.0.0', help='ホストアドレス')
    parser.add_argument('--port', type=int, default=8000, help='ポート番号')
    parser.add_argument('--reload', action='store_true', help='自動リロード有効化')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🚀 ES診断ツール（FastAPI版）起動中...")
    print("="*60)
    print(f"\n🔧 サーバー起動設定:")
    print(f"  - Host: {args.host}")
    print(f"  - Port: {args.port}")
    print(f"  - Reload: {args.reload}")
    print(f"\n🌐 アクセスURL:")
    print(f"  - メインページ: http://localhost:{args.port}")
    print(f"  - APIドキュメント: http://localhost:{args.port}/docs")
    print(f"  - ReDoc: http://localhost:{args.port}/redoc")
    print("\n💡 終了するには Ctrl+C を押してください")
    print("="*60 + "\n")

    uvicorn.run(
        "app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
