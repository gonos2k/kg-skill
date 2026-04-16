# kg-skill

> **언어 / Language:** [English](README.md) | **한국어**

[Claude Code](https://claude.ai/claude-code) 용 지식 그래프 + LLM 위키 스킬.

[Karpathy의 LLM Wiki 패턴](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)을 확장한 것으로, LLM이 구조화된 위키를 작성·유지하고 인간이 소스를 큐레이션하고 질문하는 영속적·축적형 지식 베이스입니다.

## Karpathy 패턴 대비 추가점

- **구조 그래프** — [Graphify](https://github.com/safishamsi/graphify) 기반 Leiden 클러스터링으로 커뮤니티 감지, 갓 노드, 문서 간 비자명 연결 자동 발견
- **그래프 전용 모드** — 위키 설정 없이 그래프만으로 orient/query/update 가능
- **증분 갱신** — SHA256 캐시로 변경 파일만 감지, 코드 전용 변경은 LLM 추출 건너뜀
- **검증 체인** — Graph → Wiki → Raw Source (3계층 신뢰 위계)
- **대화 운영** — LLM이 단순 서기가 아닌 사고 파트너 역할
- **진화형 온톨로지** — 7개 클래스(Artifact, Concept, Source, Procedure, Experience, Heuristic, Decision), proposal-first 스키마 변경, receipt 기반 품질 게이트

## 슬래시 커맨드

### 데이터 운영 (지식 축적)

| 커맨드 | 설명 |
|--------|------|
| `/kg` | 전체 레퍼런스 + 오리엔테이션 |
| `/kg-orient` | 세션 시작 요약 — 그래프/위키 상태, 갓 노드, 신선도 |
| `/kg-init` | 위키 디렉토리 부트스트랩 — 스키마 복사, 폴더 생성, 멱등(재실행 안전) |
| `/kg-update` | 증분 그래프 재빌드 (Graphify `--update` 위임) |
| `/kg-ingest` | 소스 파일을 위키로 인제스트 — 토론, 핵심 요약, 페이지 생성 |
| `/kg-query` | BFS/DFS 그래프 순회 + 위키 검색 |
| `/kg-lint` | 건강 점검 — 그래프 무결성, 고아 페이지, 누락 링크, 스키마 검증 |

### 대화 운영 (상호 작용)

| 커맨드 | 설명 |
|--------|------|
| `/kg-reflect` | 긴장, 새 패턴, 사각지대, 바뀐 전제 발견 |
| `/kg-challenge` | 악마의 변호인 — 위키 주장에 근거로만 반박 |
| `/kg-connect` | 커뮤니티 간 누락된 다리 발견 |
| `/kg-suggest` | 지식 갭 기반 다음 읽기/인제스트 추천 |
| `/kg-elicit` | 암묵지 추출 — 대화를 통해 경험·휴리스틱 페이지 생성 |
| `/kg-autoresearch` | 자율 다중 라운드 웹 리서치 루프 |

### 스키마 운영

| 커맨드 | 설명 |
|--------|------|
| `/kg-schema` | 온톨로지 진화 — propose/approve/migrate/diff/list |
| `/kg-canvas` | Obsidian Canvas 내보내기 — 지식 시각화 |
| `/kg-postmortem` | 시행착오 기록 — attempted → outcome → lesson 구조화 캡처 |

## 온톨로지 (v1)

7개 지식 클래스와 정형화된 프론트매터 규약.

| 클래스 | 용도 | page_kind |
|--------|------|-----------|
| **Artifact** | 코드 엔티티 (함수, 모듈, 커널) | entity, kernel, module |
| **Concept** | 도메인 개념, 이론 | concept, theory, overview |
| **Source** | 논문, 문서 요약 | paper, manual, spec |
| **Procedure** | 단계별 절차 | procedure, workflow, recipe |
| **Experience** | 시행착오 에피소드 | episode, session, incident |
| **Heuristic** | 규칙, 교훈 | rule, guideline, pattern |
| **Decision** | 설계 결정 + 근거 | decision, trade-off |

### 스키마 진화

모든 스키마 변경은 **proposal-first** 워크플로우를 따릅니다:

```
/kg-reflect (드리프트 감지)
  → /kg-schema propose (제안 생성)
    → /kg-schema approve (영수증 수집 + 게이트 판정)
      → /kg-schema apply (스키마 파일 수정)
        → /kg-schema migrate (영향 받는 페이지 마이그레이션)
```

**Receipt 기반 품질 게이트**: `validate.py --receipt`가 6개 센서를 실행합니다. Required 티어(schema_diff, template_contract, frontmatter_valid, legacy_compat, evidence_pages)가 모두 PASS여야 승인이 진행됩니다.

## 설치

스킬 디렉토리를 `~/.claude/skills/`에 복사:

```bash
cp -r kg kg-orient kg-update kg-query kg-lint kg-ingest \
      kg-reflect kg-challenge kg-connect kg-suggest \
      kg-init kg-schema kg-elicit kg-postmortem \
      kg-autoresearch kg-canvas \
      ~/.claude/skills/
```

`~/.claude/CLAUDE.md`에 추가:

```markdown
## kg (knowledge-graph)
- **kg** (`~/.claude/skills/kg/SKILL.md`) - Knowledge graph + LLM wiki.
  Sub-commands: /kg-orient, /kg-update, /kg-query, /kg-lint, /kg-ingest,
  /kg-reflect, /kg-challenge, /kg-connect, /kg-suggest
When the user types /kg or any sub-command, invoke the Skill tool with the matching skill name.
When wiki/ or graphify-out/ exists in the project, proactively orient at session start.
```

## 의존성

- [graphify](https://github.com/safishamsi/graphify) (`pip install graphifyy`) — 구조 그래프 추출
- [Obsidian](https://obsidian.md/) (선택) — 위키링크와 그래프 뷰로 위키 탐색

## 아키텍처

```
project/
├── <source-dir>/            # 계층 1: 원본 소스 (불변)
├── wiki/                    # 계층 2: LLM 유지 위키
│   ├── .schema/             #   per-wiki 스키마 핀
│   ├── .schema-proposals/   #   보류 중 스키마 제안
│   ├── index.md             #   콘텐츠 카탈로그
│   ├── hot.md               #   현재 초점 + 유지보수 부채
│   ├── overview.md          #   프로젝트 개요
│   ├── log.md               #   연대순 기록
│   ├── entities/            #   Artifact 페이지
│   ├── concepts/            #   Concept 페이지
│   ├── sources/             #   Source 페이지
│   ├── procedures/          #   Procedure 페이지
│   ├── experiences/         #   Experience 페이지
│   ├── heuristics/          #   Heuristic 페이지
│   ├── decisions/           #   Decision 페이지
│   └── queries/             #   쿼리 결과 캐시
├── graphify-out/            # 구조 그래프 계층
│   ├── graph.json           #   노드, 엣지, 커뮤니티
│   ├── manifest.json        #   증분 갱신용 해시
│   └── GRAPH_REPORT.md      #   갓 노드, 서프라이즈
└── CLAUDE.md                # 스키마 규약과 워크플로우
```

### 네이밍 규약

- **`/kg-<verb>`** (하이픈) — canonical 사용자 커맨드. 서브스킬 `trigger:` 필드가 이 형식을 사용.
- **`/kg <verb>`** (공백) — 가독성용 표기. 실제 호출 시 항상 하이픈 형식 사용.

## 상호작용 원칙

1. **비대칭 역할** — 인간은 판단과 방향을 제공하고, LLM은 회상·교차 참조·패턴 감지를 담당합니다.
2. **생산적 마찰** — 동의는 저렴합니다. 가치 있는 상호작용은 LLM이 모순, 갭, 비자명 연결을 드러낼 때 발생합니다.
3. **대화의 축적** — reflect, challenge, connect의 통찰이 위키에 다시 기록되어 대화 자체가 축적됩니다.
4. **스키마는 제품** — 스키마(`core.yaml` + `relations.yaml`)는 인프라가 아닌 도메인 모델 자체입니다. 모든 변경은 proposal-first.

## 도구

| 파일 | 용도 |
|------|------|
| `kg/schema/tools/validate.py` | 프론트매터 검증, 관계 도메인/레인지 체크, receipt 생성 |
| `kg/schema/tools/build_search_index.py` | BM25 검색 인덱스 빌드 |
| `kg/schema/core.yaml` | 클래스 정의, 인식론적 상태, 신뢰도 레벨 |
| `kg/schema/relations.yaml` | 술어 정의 + 도메인/레인지 제약 |
| `kg/schema/frontmatter.yaml` | 필드 타입 + 열거형 |
| `kg/templates/*.md` | 클래스별 페이지 템플릿 |

## 라이선스

MIT
