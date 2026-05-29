# teacher 하네스 설치 프롬프트

`hanfeni/aiceo-4th-training` 리포의 teacher 하네스를 Claude Code에 설치하는 복붙 프롬프트.
README §10-C 함정(blob→raw, WebFetch 요약 변형) 회피 — **raw URL 고정**.

---

## ⚡ 초단축 (가장 짧음 — 이거 한 줄로 충분)

```text
아래 2개 raw 파일을 원문 변형 없이 그대로 읽어 ~/.claude/ 에 설치해줘. SKILL의 "이식 절차"에 적힌 hook·settings·output-style도 그 정의대로 만들어줘.
https://raw.githubusercontent.com/hanfeni/aiceo-4th-training/main/.claude/commands/teacher.md
https://raw.githubusercontent.com/hanfeni/aiceo-4th-training/main/.claude/skills/teacher/SKILL.md
```

> 프로젝트에만 설치하려면 `~/.claude/` → `./.claude/`.

---

## 📋 표준 (자가검증 포함)

```text
아래 GitHub raw 링크 2개를 원문 그대로(요약·개선 금지) 읽어 동일 하네스를 ~/.claude/ 에 설치해줘.

1) https://raw.githubusercontent.com/hanfeni/aiceo-4th-training/main/.claude/commands/teacher.md
2) https://raw.githubusercontent.com/hanfeni/aiceo-4th-training/main/.claude/skills/teacher/SKILL.md

순서:
1. 두 파일을 변형 없이 그대로 생성: ~/.claude/commands/teacher.md, ~/.claude/skills/teacher/SKILL.md
2. SKILL.md "이식 절차"의 인라인 정의대로 자동 트리거 구성:
   - ~/.claude/hooks/teacher-session-start.sh 생성 + chmod +x
   - ~/.claude/settings.json 의 hooks.SessionStart 에 등록
3. 자가검증: /teacher 커맨드 인식 + hook JSON 유효성(exit 0) 확인 후 보고.
4. frontmatter 한 글자도 변형 금지.
```

설치 후: 재시작/`/clear` 시 자동, 또는 `/teacher` 수동 트리거.
