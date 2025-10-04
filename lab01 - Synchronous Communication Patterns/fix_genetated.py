#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修復 user_service_pb2_grpc.py 中的導入問題
將絕對導入改為相對導入
"""

import os
import sys

def fix_grpc_import():
    """修復 generated 文件中的導入"""
    
    grpc_file = 'python_grpc_lab/generated/user_service_pb2_grpc.py'
    
    if not os.path.exists(grpc_file):
        print(f"✗ 錯誤: 找不到文件 {grpc_file}")
        print("\n請確認:")
        print("1. 文件路徑正確")
        print("2. 已經生成了 protobuf 文件")
        return False
    
    print(f"找到文件: {grpc_file}")
    
    # 讀取文件內容
    with open(grpc_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否需要修復
    if 'from . import user_service_pb2' in content:
        print("✓ 文件已經是正確的相對導入，無需修改")
        return True
    
    if 'import user_service_pb2 as user__service__pb2' not in content:
        print("✗ 文件格式不符合預期")
        return False
    
    print("找到需要修復的導入語句...")
    
    # 備份原文件
    backup_file = grpc_file + '.backup'
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ 已創建備份: {backup_file}")
    
    # 替換導入語句
    old_import = 'import user_service_pb2 as user__service__pb2'
    new_import = 'from . import user_service_pb2 as user__service__pb2'
    
    new_content = content.replace(old_import, new_import)
    
    # 寫入修改後的內容
    with open(grpc_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✓ 已修復導入語句:")
    print(f"  舊的: {old_import}")
    print(f"  新的: {new_import}")
    
    return True

def test_import():
    """測試導入是否成功"""
    print("\n" + "=" * 70)
    print("測試導入...")
    print("=" * 70)
    
    try:
        from python_grpc_lab.generated import user_service_pb2, user_service_pb2_grpc
        print("✓ 導入成功！")
        print("\n可用的消息類型:")
        for attr in dir(user_service_pb2):
            if not attr.startswith('_') and attr[0].isupper():
                print(f"  - {attr}")
        
        print("\n可用的服務類:")
        for attr in dir(user_service_pb2_grpc):
            if 'Service' in attr:
                print(f"  - {attr}")
        
        return True
    except ImportError as e:
        print(f"✗ 導入失敗: {e}")
        return False

def main():
    print("=" * 70)
    print("修復 gRPC Generated 文件導入問題")
    print("=" * 70)
    print()
    
    # 檢查必要的文件
    files_to_check = [
        'python_grpc_lab/__init__.py',
        'python_grpc_lab/generated/__init__.py',
        'python_grpc_lab/generated/user_service_pb2.py',
        'python_grpc_lab/generated/user_service_pb2_grpc.py',
    ]
    
    print("檢查必要文件...")
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (缺失)")
            all_exist = False
    
    if not all_exist:
        print("\n✗ 缺少必要文件")
        print("\n請先運行:")
        print("  touch python_grpc_lab/__init__.py")
        print("  touch python_grpc_lab/generated/__init__.py")
        return 1
    
    print("\n" + "=" * 70)
    print("修復導入語句...")
    print("=" * 70)
    
    if not fix_grpc_import():
        print("\n✗ 修復失敗")
        return 1
    
    print("\n✓ 修復成功!")
    
    # 測試導入
    if test_import():
        print("\n" + "=" * 70)
        print("✓ 所有檢查通過！")
        print("=" * 70)
        print("\n現在可以運行:")
        print("  python benchmark.py")
        print()
        return 0
    else:
        print("\n✗ 導入測試失敗")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n操作被取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)