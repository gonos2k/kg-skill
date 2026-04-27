# kg-skill

> **언어 / Language:** [English](README.md) | **한국어**

[Claude Code](https://claude.ai/claude-code)용 지식 그래프 + LLM 위키 스킬 세트.

프로젝트마다 **영속적·축적형 지식 베이스**를 만듭니다. LLM은 구조화된 위키를 큐레이션하고, [Graphify](https://github.com/safishamsi/graphify)는 구조 그래프를 추출하며, **5공식 표준을 따르는 18개의 결정론적 슬래시 커맨드**가 두 계층을 동기화합니다.

[Andrej Karpathy의 LLM Wiki 패턴](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)에서 출발해 7-class 온톨로지, proposal-first 스키마 진화, receipt 기반 품질 게이트, graphify v0.5.0+ MCP 통합으로 확장.

---

## 왜 도움이 될 수 있나

이미 갖고 계신 조각들이 있을 겁니다:

- **논문/코드/노트가 쌓인 폴더** — 그런데 무엇이 무엇과 연결되는지 잊어버림
- **희미한 기억** — "6개월 전에 이거랑 비슷한 거 봤는데..."
- **점점 커지는 위키** — 그런데 코드나 본인의 이해와 점점 어긋남
- **여러 AI 세션** — 매번 처음부터 다시 시작

`kg-skill`은 Claude에게 **세션을 가로질러 기억하는 단일·구조화된 방법**을 줍니다:

```text
사용자             kg-skill                    Claude (세션 간)
────────          ─────────────────           ──────────────────────
"이 논문 인제스트" → /kg-ingest paper.pdf  →   논문 내용을 알고 기존 개념과 연결
"왜 X였지?"        → /kg-query --depth deep → 과거 결정 + 근거 인용
"위키 점검"        → /kg-reflect           → 보지 못한 긴장 발견
"감사"            → /kg-lint              → 깨진 링크, stale claim, 스키마 드리프트 검출
```

가능한 곳은 **결정론적**(BM25 검색, 그래프 순회, 검증 스크립트), 권한이 중요한 곳은 **인간 게이트**(스키마 변경, 페이지 삭제, 소스 승인) — 이 분리가 핵심입니다.

---

## 5분 안에 시작하기

```bash
# 1. graphify 설치 (그래프 추출 백엔드)
pip install graphifyy

# 2. kg-skill을 Claude에 설치
git clone https://github.com/gonos2k/kg-skill.git ~/kg-skill-source
cd ~/kg-skill-source
cp -r kg kg-* ~/.claude/skills/

# 3. Claude Code에서 위키 부트스트랩
/kg-init

# 4. 논문이나 코드를 raw/에 넣고 인제스트
/kg-ingest raw/my-paper.pdf

# 5. 질문하기
/kg-query "이 논문이 X에 대해 뭐라고 하지?"

# 6. 몇 번 인제스트한 뒤 통찰 surfacing
/kg-reflect
```

이게 전부입니다. 모든 스킬이 동일한 5공식 구조를 따르고 예측 가능한 Output Contract를 출력합니다.

---

## 5공식 표준

모든 `kg-*` 스킬은 같은 구조라서 Claude의 동작이 일관됩니다:

| 섹션 | 답하는 것 |
|---|---|
| **YAML Trigger** | 이 스킬은 언제 켜져야 하는가? (구체적 phrase, 프로젝트 상태) |
| **Activate When / Do Not Activate When** | 명시적 양/음 트리거 — 스킬 충돌 방지 |
| **Workflow** | "stop condition"을 포함한 단계별 절차 |
| **Output Contract** | 표준 필드(`Confidence:`, `Caveats:`, `Next command:`)를 가진 fenced `text` 블록. [`kg/references/output-contract-standard.md`](kg/references/output-contract-standard.md) 참조 |
| **Examples + Exceptions and Escalation** | 구체적 사용 예시 + 모든 escape hatch 차단 (예: "사용자 'yes'는 승인 아님") |

권한이 중요한 곳에서 **LLM이 임의로 행동할 수 없게** 만든 설계. 어떤 `/kg-*` 명령을 켜도 같은 형식이 나옵니다.

---

## 슬래시 커맨드 (18개)

### 데이터 운영 — 지식 축적

| 커맨드 | 용도 |
|---|---|
| `/kg-init` | 위키 부트스트랩 (스키마, 폴더, 인덱스). 멱등(재실행 안전). |
| `/kg-ingest` | 소스 읽기 → 핵심 토론 → source/entity/concept 페이지 작성 + [[wikilink]]. |
| `/kg-update` | 그래프 증분 재빌드 (`graphify <path> --update` 위임). |
| `/kg-query` | BFS/DFS 순회 + 위키 검색. `--depth quick\|standard\|deep`. |
| `/kg-lint` | 건강 점검 — 고아 페이지, 깨진 링크, stale claim, proposal debt. |
| `/kg-orient` | read-only 세션 시작 요약 (hot.md, 그래프 통계, 신선도). |

### 대화 운영 — LLM을 사고 파트너로

| 커맨드 | 용도 |
|---|---|
| `/kg-reflect` | 긴장, 새 패턴, 사각지대, 스키마 드리프트 surfacing. 요약이 아니라 비자명 통찰만. |
| `/kg-challenge` | 악마의 변호인. **기존 근거만으로** 위키 주장 반박. |
| `/kg-connect` | 그래프 커뮤니티 간 누락 다리 발견. 자동으로 엣지 추가 안 함. |
| `/kg-suggest` | 실제 지식 갭 기반 다음 자료/액션 추천. |
| `/kg-elicit` | 대화로 암묵지 캡처 → Experience(항상) + 선택적 Heuristic. |
| `/kg-postmortem` | 최근 구체적 실패용 더 엄격한 `/kg-elicit` (에러 텍스트 verbatim 보존). |
| `/kg-autoresearch` | 감독 하의 다중 라운드 웹 리서치. 명시적 사용자 승인까지 큐만 작성 — 자동 인제스트 절대 금지. |

### 거버넌스 & 통합

| 커맨드 | 용도 |
|---|---|
| `/kg-schema` | 온톨로지 진화 — `propose`, `approve`, `apply`, `migrate`, `diff`, `list`, `pull-global`. Receipt-gated. |
| `/kg-canvas` | 위키를 Obsidian Canvas (`.canvas` JSON)로 내보내기. read-only. |
| `/kg-merge` | **신규** — `graphify merge-graphs`로 cross-project KG (여러 repo → 통합 그래프). |
| `/kg-mcp` | **신규** — `.mcp.json`에 `graphify --mcp` 등록 → 다른 스킬이 graph.json 재로딩 없이 MCP 도구로 그래프 쿼리. `--apply` Authority gate. |

### 라우터

| 커맨드 | 용도 |
|---|---|
| `/kg` | 라우터 — 시스템 설명 또는 적절한 sub-command로 안내. 직접 실행은 안 함. |

---

## 온톨로지 (v1) — 7개 클래스

각 위키 페이지는 정형 frontmatter를 가진 한 클래스입니다:

| 클래스 | 용도 | 폴더 |
|---|---|---|
| **Artifact** | 코드 엔티티 (함수, 모듈, 커널) | `wiki/entities/` |
| **Concept** | 도메인 개념, 이론 | `wiki/concepts/` |
| **Source** | 논문 / 문서 / URL 요약 | `wiki/sources/` |
| **Procedure** | 단계별 절차 | `wiki/procedures/` |
| **Experience** | 시행착오 에피소드 (verbatim 보존) | `wiki/experiences/` |
| **Heuristic** | 정제된 rule of thumb | `wiki/heuristics/` |
| **Decision** | 근거 있는 설계 결정 | `wiki/decisions/` |

### 스키마 진화 (proposal-first)

```text
/kg-reflect (드리프트 감지)
    → /kg-schema propose (제안 작성)
        → /kg-schema approve (영수증 수집 + 6-sensor 게이트)
            → /kg-schema apply (영수증 PASS인 경우만)
                → /kg-schema migrate (영향 받는 페이지 마이그레이션)
```

**Authority Matrix** ([`kg/references/authority-matrix.md`](kg/references/authority-matrix.md))

| 액션 | 권한 | 이유 |
|---|---|---|
| 스키마 변경 | **Human** | 온톨로지는 contract |
| 페이지 재분류 / 삭제 | **Human** | 폴더 변경 = identity 변경 |
| Source 승인 (autoresearch) | **Human** | provenance 무결성 |
| Experience → Heuristic 승격 | **Human** | 일반화는 판단 |
| `hot.md` / `log.md` / `_index.md` 갱신 | **LLM** | 재생성 가능한 bookkeeping |
| `pull-global` 호환 변경 | **LLM (dry-run 우선)** | 항상 미리보기 |

---

## 아키텍처

```text
project/
├── <source-dir>/             # 계층 1 — 원본 소스 (불변)
│   └── (자동 감지: gMeso/vault/, raw/, docs/, 또는 .)
├── wiki/                     # 계층 2 — LLM 유지 위키
│   ├── .schema/              #   per-wiki 스키마 핀 (/kg-init이 복사)
│   ├── .schema-proposals/    #   pending proposal + 영수증
│   ├── .research-queue/      #   /kg-autoresearch staging (approved/rejected)
│   ├── index.md              #   콘텐츠 카탈로그 (마지막 수단 read)
│   ├── hot.md                #   ~500단어 세션 컨텍스트 캐시
│   ├── overview.md           #   안정된 글로벌 synthesis
│   ├── log.md                #   append-only 운영 history
│   ├── entities/             #   Artifact 페이지
│   ├── concepts/             #   Concept 페이지
│   ├── procedures/           #   Procedure 페이지
│   ├── experiences/          #   Experience 페이지
│   ├── heuristics/           #   Heuristic 페이지
│   ├── decisions/            #   Decision 페이지
│   ├── sources/              #   Source 요약
│   └── queries/              #   filed query 결과
└── graphify-out/             # 구조 그래프 계층 (graphify v0.5.0+)
    ├── graph.json            #   NetworkX node_link_data
    ├── GRAPH_REPORT.md       #   갓 노드, 커뮤니티, surprises
    ├── graph.html            #   대화형 HTML (default)
    ├── manifest.json         #   증분 갱신용 SHA256 manifest
    ├── memory/               #   Q&A 피드백 루프
    ├── merged-graph.json     #   cross-repo merge 결과
    └── (선택: graph.svg, graph.graphml, cypher.txt)
```

### 검증 체인

**Graph → Wiki → Raw Source**가 신뢰 위계입니다. 위키는 **derived**, 원본 소스가 **authoritative**. `/kg-query`는 결정에 영향 주는 답에는 raw source를 인용합니다.

### 두 가지 운영 모드

- **Graph-only**: `graphify-out/`만 존재. `/kg-orient`, `/kg-query`, `/kg-update` 단독 작동.
- **Graph + Wiki**: 둘 다 존재. 위키가 구조 그래프 위에 의미 깊이를 더함.

---

## References 라이브러리

`kg/references/` — Claude가 필요할 때만 읽음 (progressive disclosure):

| 파일 | 주제 |
|---|---|
| [`architecture.md`](kg/references/architecture.md) | 레이아웃, 소스 감지, 페이지 템플릿, 기술 노트 |
| [`ontology.md`](kg/references/ontology.md) | 7 클래스, page_kind, instance_of, schema-as-product, proposal/receipt |
| [`authority-matrix.md`](kg/references/authority-matrix.md) | Human vs LLM 권한, hot.md 우선순위, novelty test |
| [`context-compression.md`](kg/references/context-compression.md) | BM25 검색, hot/overview/_index 위계, archive 정책 |
| [`schema-evolution.md`](kg/references/schema-evolution.md) | 마이그레이션 정책, supersession, convergence tracking |
| [`codex-integration.md`](kg/references/codex-integration.md) | 양방향 Codex 파이프라인 (review filing, domain context injection) |
| [`output-contract-standard.md`](kg/references/output-contract-standard.md) | 표준 Output Contract 필드명 — `Next command:`, `Confidence:`, `Caveats:` |

---

## Helper 도구

`kg/schema/tools/` — 결정론적 헬퍼가 LLM 판단 부담을 줄여줍니다:

| 스크립트 | 용도 |
|---|---|
| `validate.py` | frontmatter 검증, relation domain/range 체크, receipt 생성 |
| `build_search_index.py` | BM25 검색 인덱스 빌더 (한국어+영어 CJK 토크나이저) |
| `check_skill_frontmatter.py` | 모든 SKILL.md 검증 (YAML, 필수 키, trigger equality, body forbidden 패턴) |
| `kg_lint.py` | 위키 sensor — 고아 페이지, 누락 wikilink, deprecated-without-callout, supersession 고아 |
| `extract_claims.py` | `> [!claim]`, `> [!evidence]`, `> [!tension]` 콜아웃 → JSON (`/kg-query`, `/kg-challenge` 사용) |

---

## graphify 통합 (soft dependency)

11개 sub-skill이 [graphify](https://github.com/safishamsi/graphify) v0.5.0+가 있으면 자동 사용, 없거나 stale이면 우아하게 fallback.

**Freshness gate**: `graphify-out/graph.json`은 `mtime < 7일`일 때만 authoritative로 취급. stale 그래프는 wiki-only / BM25-only 경로로 강등되고 `Caveats:`에 stale 표기.

**MCP 서버 도구** (`graphify <path> --mcp`):

| 도구 | 사용처 |
|---|---|
| `query_graph` | `/kg-query` (token budget 있는 BFS/DFS) |
| `get_node` / `get_neighbors` | `/kg-challenge`, `/kg-elicit` |
| `get_community` | `/kg-connect`, `/kg-suggest` |
| `god_nodes` | `/kg-orient`, `/kg-suggest` |
| `graph_stats` | `/kg-orient`, `/kg-lint` |
| `shortest_path` | `/kg-ingest` (confirmation gate), `/kg-postmortem` (패턴 감지), `/kg-connect` (객관적 거리) |

`/kg-mcp register --scope project --apply`로 MCP 서버 등록.

---

## 설치

### 요구사항

- Python ≥ 3.10
- [graphify](https://github.com/safishamsi/graphify) v0.5.0+: `pip install graphifyy`
- [Obsidian](https://obsidian.md/) (선택, 그래프 뷰로 위키 탐색)

### 스킬 설치

```bash
git clone https://github.com/gonos2k/kg-skill.git
cd kg-skill
cp -r kg kg-* ~/.claude/skills/
```

### `~/.claude/CLAUDE.md`에 추가

```markdown
## kg (knowledge-graph)
- **kg** (`~/.claude/skills/kg/SKILL.md`) — Knowledge graph + LLM wiki router.
  Sub-commands: /kg-orient, /kg-update, /kg-query, /kg-lint, /kg-ingest,
  /kg-reflect, /kg-challenge, /kg-connect, /kg-suggest, /kg-elicit,
  /kg-postmortem, /kg-schema, /kg-autoresearch, /kg-canvas, /kg-merge, /kg-mcp.
When the user types /kg or any sub-command, invoke the Skill tool with the matching skill name.
When wiki/ or graphify-out/ exists in the project, the kg-orient skill auto-suggests at session start.
```

### 설치 검증

```bash
python3 ~/.claude/skills/kg/schema/tools/check_skill_frontmatter.py
# 예상: PASS — 18 SKILL.md files OK
```

---

## 네이밍 규약

- **`/kg-<verb>`** (하이픈) — canonical 사용자 커맨드. 항상 이 형식 사용.
- **`/kg <verb>`** (공백) — 사용 안 함; 모든 sub-skill의 `trigger:` 필드는 하이픈 형식이 ground truth.

---

## 상호작용 원칙

1. **비대칭 역할** — 인간은 판단·방향을 제공, LLM은 회상·교차 참조·패턴 감지를 담당.
2. **생산적 마찰** — 동의는 저렴함. 가치는 LLM이 모순·갭·비자명 연결을 드러낼 때 발생.
3. **대화의 축적** — `/kg-reflect`, `/kg-challenge`, `/kg-connect`의 통찰이 위키에 다시 기록되어 대화 자체가 축적.
4. **스키마는 제품** — `core.yaml` + `relations.yaml`은 인프라가 아니라 도메인 모델. 모든 변경 proposal-first.
5. **결정론 > LLM 판단** — 스크립트로 가능한 검증(BM25, 그래프 거리, frontmatter 검증)은 스크립트로. LLM 판단은 콘텐츠 질문 전용.

---

## 실제 사용 패턴

스킬 셋은 네 가지 관찰을 중심으로 설계되어 있습니다:

1. **삭제 대신 supersession** — 새 근거가 기존 주장을 뒤집을 때, 옛 페이지는 권위 대체 페이지로 향하는 `[SUPERSEDED]` callout과 함께 보존됩니다. Git 이력이 아니라 위키 자체가 audit trail입니다.

2. **생산적 마찰이 곧 산출물** — `/kg-challenge`와 `/kg-reflect`는 합의가 아니라 의견 충돌을 만들도록 설계되어 있습니다. Tension callout과 근거 인용 claim 덕분에 정정이 깔끔하게 적용됩니다.

3. **적대적 검토는 짧은 프롬프트 × 병렬을 선호** — 외부 LLM 비판은 길게 종합한 단일 프롬프트보다 짧은·단일 질문·병렬 검토일 때 더 신뢰할 수 있습니다. [`kg/references/codex-integration.md`](kg/references/codex-integration.md) 참조.

4. **`Caveats:` 는 협상 불가** — 모든 Output Contract는 `Caveats:` 줄을 포함합니다. *수정 불가능한* 발견이 사는 곳이 거기입니다 — 이 필드는 수정 불가 이슈를 조용히 빠뜨리려는 유혹을 차단합니다.

---

## 라이선스

MIT
