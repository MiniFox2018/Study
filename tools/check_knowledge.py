#!/usr/bin/env python3
"""Study 离线结构检查。只验证可机械核对的性质，不证明知识完全正确。"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'!?\[[^\]\n]*\]\((<[^>\n]+>|[^\s)]+)(?:\s+["\x27][^\n]*?["\x27])?\)')
HTML_LINK = re.compile(r'\b(?:src|href)=["\x27]([^"\x27]+)["\x27]')
REF = re.compile(r'^\s{0,3}\[(?!\^)[^\]\n]+\]:\s*(<[^>\n]+>|\S+)', re.M)


def main_doc(path: Path) -> bool:
    return '来源保全' not in path.relative_to(ROOT).as_posix()


def without_code(text: str) -> tuple[str, bool]:
    """保留行号并屏蔽围栏/行内代码，防止把教学样例当链接。"""
    out, fence = [], None
    for line in text.splitlines(keepends=True):
        m = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if fence:
            if m and m[1][0] == fence[0] and len(m[1]) >= len(fence) and not line[m.end():].strip():
                fence = None
            out.append('\n' if line.endswith('\n') else '')
        elif m:
            fence = m[1]
            out.append('\n' if line.endswith('\n') else '')
        else:
            out.append(re.sub(r'(`+)[^`\n]*?\1', lambda x: ' ' * len(x[0]), line))
    return ''.join(out), fence is not None


def anchors(text: str) -> set[str]:
    result, counts = set(), {}
    for line in text.splitlines():
        m = re.match(r'^#{1,6}\s+(.+?)\s*#*$', line)
        if not m:
            continue
        title = re.sub(r'<[^>]+>', '', html.unescape(m[1])).lower()
        slug = ''.join(c for c in title if c in '_-' or c.isspace() or unicodedata.category(c)[0] in 'LNM')
        slug = re.sub(r'\s', '-', slug)
        n = counts.get(slug, 0)
        result.add(slug if n == 0 else f'{slug}-{n}')
        counts[slug] = n + 1
    result.update(re.findall(r'\b(?:id|name)=["\x27]([^"\x27]+)', text))
    return result


def run() -> int:
    parser = argparse.ArgumentParser(description='检查 Study 的本地链接、Markdown 结构、公式损坏迹象和来源校验值')
    parser.add_argument('--json', dest='json_path', help='另存中文检查结果 JSON；默认只输出终端摘要')
    args = parser.parse_args()
    errors, notices = [], []
    docs = sorted(p for p in ROOT.rglob('*.md') if '.git' not in p.parts)
    link_count = 0

    def issue(p: Path, line: int, kind: str, detail: str) -> None:
        errors.append({'文件': p.relative_to(ROOT).as_posix(), '行': line, '类型': kind, '说明': detail})

    for p in docs:
        text = p.read_text(encoding='utf-8')
        clean, unclosed = without_code(text)
        if main_doc(p):
            if unclosed:
                issue(p, 1, '代码围栏', '存在未闭合的围栏')
            if len(re.findall(r'^# ', clean, re.M)) != 1:
                issue(p, 1, '标题', '主库文档应有且只有一个一级标题')
            bad = re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', text)
            if bad:
                issue(p, text[:bad.start()].count('\n') + 1, '控制字符', repr(bad[0]))
            for n, line in enumerate(clean.splitlines(), 1):
                if line.strip() in ('[', ']'):
                    issue(p, n, '公式损坏迹象', '孤立方括号；请人工确认是否为丢失的数学分隔符')
            if len(re.findall(r'^\s*\$\$\s*$', clean, re.M)) % 2:
                issue(p, 1, '数学分隔符', '独占行 $$ 未成对')
            if re.search(r'结构基线|暂无增补|暂无补充|待后续补充正文', clean):
                issue(p, 1, '占位内容', '发现未完成的教学占位文字')
        matches = [(m.start(), m[1].strip('<>')) for pat in (LINK, HTML_LINK, REF) for m in pat.finditer(clean)]
        for pos, dest in matches:
            dest = html.unescape(dest)
            try:
                parsed = urlsplit(dest)
            except ValueError:
                issue(p, clean[:pos].count('\n') + 1, '链接格式', dest)
                continue
            if parsed.scheme or dest.startswith('//'):
                continue
            link_count += 1
            target = (p.parent / unquote(parsed.path)).resolve() if parsed.path else p
            line = clean[:pos].count('\n') + 1
            if not target.is_relative_to(ROOT):
                issue(p, line, '链接越界', dest)
            elif not target.exists():
                issue(p, line, '本地链接缺失', dest)
            elif main_doc(p) and parsed.fragment and target.suffix == '.md':
                if unquote(parsed.fragment).removeprefix('user-content-') not in anchors(target.read_text()):
                    issue(p, line, '标题锚点', dest)

    notebooks, empty_notebooks = 0, 0
    allowed_empty = '来源保全/Data-Science-For-Beginners/课程/5-Data-Science-In-Cloud/19-Azure/solution/notebook.ipynb'
    for p in ROOT.rglob('*.ipynb'):
        if '.git' in p.parts:
            continue
        if p.relative_to(ROOT).as_posix() == allowed_empty and p.stat().st_size == 0:
            empty_notebooks += 1
            notices.append('第 19 课解答 Notebook 是已登记的上游空文件；不能运行。')
            continue
        try:
            obj = json.loads(p.read_text())
            if obj.get('nbformat') != 4 or not isinstance(obj.get('cells'), list):
                raise ValueError('不是带 cells 的 nbformat 4 Notebook')
            if obj.get('nbformat_minor', 0) >= 5 and any(not c.get('id') for c in obj['cells']):
                raise ValueError('nbformat 4.5 或更高版本缺少单元 id')
            notebooks += 1
        except (ValueError, OSError) as exc:
            issue(p, 1, 'Notebook 结构', str(exc))

    svg_count = 0
    for p in ROOT.rglob('*.svg'):
        try:
            ET.parse(p)
            svg_count += 1
        except (ET.ParseError, OSError) as exc:
            issue(p, 1, 'SVG XML 格式', str(exc))

    ledger = ROOT / '维护/来源完整性.json'
    checked_sources = 0
    if not ledger.exists():
        issue(ledger, 1, '来源记录', '来源完整性记录缺失')
    else:
        data = json.loads(ledger.read_text())
        for name, record in data['保全文件校验'].items():
            p = (ROOT / name).resolve()
            if not p.is_relative_to(ROOT) or not p.is_file():
                issue(p if p.is_relative_to(ROOT) else ledger, 1, '来源文件缺失', name)
            elif hashlib.sha256(p.read_bytes()).hexdigest() != record['当前_sha256']:
                issue(p, 1, '来源校验值变化', '先审查实际差异，再有依据地更新校验记录，不能直接重新计算掩盖变化')
            checked_sources += 1
        actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and '来源保全' in str(p.relative_to(ROOT))}
        for name in sorted(actual - data['保全文件校验'].keys()):
            issue(ROOT/name, 1, '来源未登记', '新增保全文件需要记录来源和校验值')

    result = {'说明': '结构检查不替代语义、外链在线状态和实验运行验证', 'Markdown总数': len(docs),
              '主库Markdown': sum(main_doc(p) for p in docs), '本地链接检查次数': link_count,
              '有效Notebook': notebooks, '已登记上游空Notebook': empty_notebooks,
              '来源文件校验数': checked_sources, '有效SVG': svg_count, '错误': errors, '提示': notices}
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(f'检查文档 {len(docs)} 篇（主库 {result["主库Markdown"]} 篇），本地链接 {link_count} 处。')
    print(f'Notebook：{notebooks} 个结构有效，{empty_notebooks} 个已登记空文件；SVG：{svg_count} 个有效；来源校验：{checked_sources} 个。')
    for item in errors[:50]:
        print(f'错误：{item["文件"]}:{item["行"]} [{item["类型"]}] {item["说明"]}')
    if len(errors) > 50:
        print(f'另有 {len(errors)-50} 项错误；用 --json 查看全部。')
    for notice in notices:
        print('提示：' + notice)
    print('结果：' + ('未通过，共 ' + str(len(errors)) + ' 项错误。' if errors else '结构检查通过。专业结论及运行结果需另行核验。'))
    return bool(errors)


if __name__ == '__main__':
    sys.exit(run())
