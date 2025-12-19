#!/usr/bin/env python3
"""
检查并修复views_formatted字段
如果views_formatted为空但views_count有值，则格式化并更新
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliUp
from bilibili_client import format_number

def check_and_fix_views_formatted():
    """检查并修复views_formatted字段"""
    print("=" * 60)
    print("检查并修复views_formatted字段")
    print("=" * 60)
    
    session = get_bilibili_session()
    try:
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        
        print(f"\n检查 {len(ups)} 个UP主\n")
        
        fixed_count = 0
        for up in ups:
            # 检查views_formatted是否为空
            needs_fix = False
            if (not up.views_formatted or up.views_formatted == '0') and up.views_count and up.views_count > 0:
                needs_fix = True
                old_formatted = up.views_formatted
                up.views_formatted = format_number(up.views_count)
                print(f"✅ {up.name}")
                print(f"   views_count: {up.views_count:,}")
                print(f"   views_formatted: {old_formatted} → {up.views_formatted}")
                fixed_count += 1
            else:
                print(f"✓  {up.name} - views_formatted: {up.views_formatted or 'NULL'}")
        
        if fixed_count > 0:
            session.commit()
            print(f"\n✅ 成功修复 {fixed_count} 个UP主的views_formatted字段")
        else:
            print(f"\n✓ 所有views_formatted字段都已正确")
        
        print("\n" + "=" * 60)
        print("修复完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    check_and_fix_views_formatted()

