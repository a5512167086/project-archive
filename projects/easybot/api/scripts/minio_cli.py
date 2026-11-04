from shared.clients.minio import minio_client


def delete_all_buckets():
    try:
        buckets = list(minio_client.list_buckets())
        print(f"找到 {len(buckets)} 個 bucket")

        for bucket in buckets:
            bucket_name = bucket.name
            print(f"正在處理 bucket: {bucket_name}")

            try:
                objects = minio_client.list_objects(bucket_name, recursive=True)
                object_names = [obj.object_name for obj in objects]

                if object_names:
                    print(f"  - 刪除 {len(object_names)} 個物件")
                    errors = minio_client.remove_objects(bucket_name, object_names)
                    for error in errors:
                        print(f"    錯誤: {error}")
                else:
                    print(f"  - bucket '{bucket_name}' 為空")

                minio_client.remove_bucket(bucket_name)
                print(f"  成功刪除 bucket '{bucket_name}'")

            except Exception as e:
                print(f"  刪除 bucket '{bucket_name}' 時發生錯誤: {e}")

        print("所有 bucket 處理完成")

    except Exception as e:
        print(f"獲取 bucket 列表時發生錯誤: {e}")


def list_all_buckets():
    try:
        buckets = list(minio_client.list_buckets())
        print(f"總共有 {len(buckets)} 個 bucket:")

        for i, bucket in enumerate(buckets, 1):
            bucket_name = bucket.name
            created_date = bucket.creation_date
            print(f"{i}. {bucket_name} (創建日期: {created_date})")

            try:
                objects = list(minio_client.list_objects(bucket_name, recursive=True))
                print(f"   - 包含 {len(objects)} 個物件")

                if objects:
                    for j, obj in enumerate(objects[:3]):
                        print(f"     • {obj.object_name}")
                    if len(objects) > 3:
                        print(f"     ... 還有 {len(objects) - 3} 個物件")

            except Exception as e:
                print(f"   - 無法讀取物件列表: {e}")

            print()

    except Exception as e:
        print(f"獲取 bucket 列表時發生錯誤: {e}")


def delete_specific_buckets(bucket_names):
    for bucket_name in bucket_names:
        print(f"正在刪除 bucket: {bucket_name}")

        try:
            if not minio_client.bucket_exists(bucket_name):
                print(f"  ✗ bucket '{bucket_name}' 不存在")
                continue

            objects = minio_client.list_objects(bucket_name, recursive=True)
            object_names = [obj.object_name for obj in objects]

            if object_names:
                print(f"  - 刪除 {len(object_names)} 個物件")
                errors = minio_client.remove_objects(bucket_name, object_names)
                for error in errors:
                    print(f"    錯誤: {error}")

            minio_client.remove_bucket(bucket_name)
            print(f"  ✓ 成功刪除 bucket '{bucket_name}'")

        except Exception as e:
            print(f"  ✗ 刪除 bucket '{bucket_name}' 時發生錯誤: {e}")


def interactive_delete():
    list_all_buckets()

    print("選擇操作:")
    print("1. 刪除所有 bucket")
    print("2. 刪除特定 bucket")
    print("3. 取消")

    choice = input("請選擇 (1-3): ").strip()

    if choice == "1":
        confirm = input(
            "確定要刪除所有 bucket 嗎？這個操作無法復原！(輸入 'YES' 確認): "
        )
        if confirm == "YES":
            delete_all_buckets()
        else:
            print("操作已取消")

    elif choice == "2":
        bucket_names = input("請輸入要刪除的 bucket 名稱 (用逗號分隔): ").strip()
        if bucket_names:
            bucket_list = [name.strip() for name in bucket_names.split(",")]
            confirm = input(
                f"確定要刪除這些 bucket 嗎？{bucket_list} (輸入 'YES' 確認): "
            )
            if confirm == "YES":
                delete_specific_buckets(bucket_list)
            else:
                print("操作已取消")
        else:
            print("未輸入 bucket 名稱")

    else:
        print("操作已取消")


if __name__ == "__main__":
    interactive_delete()
