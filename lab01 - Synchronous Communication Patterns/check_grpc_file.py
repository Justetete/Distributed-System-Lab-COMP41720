#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速檢查 gRPC 文件位置和導入
"""

import os
import sys

print("=" * 70)
print("檢查 python_grpc_lab 目錄結構")
print("=" * 70)

# 檢查目錄
base_dir = 'python_grpc_lab'

if not os.path.exists(base_dir):
    print(f"\n✗ 錯誤: '{base_dir}' 目錄不存在")
    print(f"當前目錄: {os.getcwd()}")
    print("\n請確認:")
    print("1. 你在正確的目錄中運行此腳本")
    print("2. 目錄名稱確實是 'python_grpc_lab'")
    sys.exit(1)

print(f"\n✓ 找到目錄: {base_dir}")
print(f"\n目錄內容:")

# 列出所有文件
for root, dirs, files in os.walk(base_dir):
    level = root.replace(base_dir, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')

# 檢查生成的文件位置
print("\n" + "=" * 70)
print("檢查生成的 protobuf 文件")
print("=" * 70)

locations = [
    f'{base_dir}/user_service_pb2.py',
    f'{base_dir}/user_service_pb2_grpc.py',
    f'{base_dir}/generated/user_service_pb2.py',
    f'{base_dir}/generated/user_service_pb2_grpc.py',
]

found_location = None
for loc in locations:
    if os.path.exists(loc):
        print(f"\n✓ 找到: {loc}")
        if 'user_service_pb2.py' in loc:
            found_location = os.path.dirname(loc)
    else:
        print(f"✗ 不存在: {loc}")

# 測試導入
print("\n" + "=" * 70)
print("測試導入")
print("=" * 70)

if found_location:
    print(f"\n發現文件在: {found_location}")
    
    # 測試不同的導入方式
    print("\n測試方法 1: 從 python_grpc_lab.generated 導入")
    try:
        from python_grpc_lab.generated import user_service_pb2, user_service_pb2_grpc
        print("✓ 成功! 使用這個導入方式:")
        print("  from python_grpc_lab.generated import user_service_pb2, user_service_pb2_grpc")
    except ImportError as e:
        print(f"✗ 失敗: {e}")
    
    print("\n測試方法 2: 從 python_grpc_lab 直接導入")
    try:
        from python_grpc_lab import user_service_pb2, user_service_pb2_grpc
        print("✓ 成功! 使用這個導入方式:")
        print("  from python_grpc_lab import user_service_pb2, user_service_pb2_grpc")
    except ImportError as e:
        print(f"✗ 失敗: {e}")
    
    print("\n測試方法 3: 添加路徑後直接導入")
    try:
        sys.path.insert(0, found_location)
        import user_service_pb2
        import user_service_pb2_grpc
        print("✓ 成功! 使用這個方式:")
        print(f"  sys.path.insert(0, '{found_location}')")
        print("  import user_service_pb2")
        print("  import user_service_pb2_grpc")
    except ImportError as e:
        print(f"✗ 失敗: {e}")

else:
    print("\n✗ 沒有找到生成的 protobuf 文件")
    print("\n你需要生成這些文件。根據你的目錄結構，選擇以下命令之一:")
    
    print("\n選項 1: 生成到 generated 子目錄 (推薦)")
    print("  cd python_grpc_lab")
    print("  mkdir -p generated")
    print("  touch generated/__init__.py")
    print("  python -m grpc_tools.protoc -I./proto --python_out=./generated --grpc_python_out=./generated ./proto/user_service.proto")
    print("  cd ..")
    
    print("\n選項 2: 生成到 python_grpc_lab 根目錄")
    print("  cd python_grpc_lab")
    print("  python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/user_service.proto")
    print("  cd ..")

# 檢查 __init__.py
print("\n" + "=" * 70)
print("檢查 __init__.py 文件")
print("=" * 70)

init_files = [
    f'{base_dir}/__init__.py',
    f'{base_dir}/generated/__init__.py',
]

for init_file in init_files:
    if os.path.exists(init_file):
        print(f"✓ 存在: {init_file}")
    else:
        print(f"✗ 不存在: {init_file} (可能需要創建)")

print("\n" + "=" * 70)
print("建議")
print("=" * 70)

print("\n如果你的文件在 python_grpc_lab/generated/ 下:")
print("1. 確保 python_grpc_lab/__init__.py 存在")
print("2. 確保 python_grpc_lab/generated/__init__.py 存在")
print("3. 使用導入: from python_grpc_lab.generated import user_service_pb2, user_service_pb2_grpc")

print("\n如果你的文件在 python_grpc_lab/ 下:")
print("1. 確保 python_grpc_lab/__init__.py 存在")
print("2. 使用導入: from python_grpc_lab import user_service_pb2, user_service_pb2_grpc")

print("\n創建 __init__.py 文件:")
print("  touch python_grpc_lab/__init__.py")
print("  touch python_grpc_lab/generated/__init__.py")

print("\n" + "=" * 70)