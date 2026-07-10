# skill-prompt-review (Claude Code 에디션)

> [English](README.md) · **한국어**

**프롬프트나 스킬에는 단위 테스트가 없습니다 — 그래서 무언가 잘못돼도 자동으로 알려주는
신호가 없습니다.** AI가 작성한 프롬프트는 특유의 방식으로 망가집니다. 작성 대화의
프레이밍을 산출물에 그대로 끌고 오고, 날짜와 일회성 사례를 박아 넣고, 존재하지도 않는
그럴듯한 플래그를 단정하며, 독자가 필요 없는 장식을 잔뜩 붙입니다 — 그리고 저자는 자기
글을 다시 읽어도 이 중 어느 것도 보지 못합니다. `skill-prompt-review`가 바로 그 빠진
점검입니다. `SKILL.md`나 프롬프트를 읽어, Anthropic·OpenAI·Google의 자체
프롬프트 엔지니어링 가이드에서 추출한 체크리스트([docs/RESEARCH.md](docs/RESEARCH.md)
참고)와 대조하고, 기준별 PASS / FAIL / N-A 리포트를 근거와 구체적 수정안과 함께
돌려줍니다.

Claude Code에서 동작합니다: 대상을 주면 텍스트를 심사합니다. 대상을 **실행하지 않으며**,
통과가 곧 보안 승인은 아닙니다.

## 왜 *fresh eye*인가

이걸 작동하게 하는 단 하나의 규칙: **자기 초안을 리뷰하지 마라.** 저자는 자기 논리의
빈틈에 스스로 의도를 채워 넣습니다. 리뷰는 대상을 쓰지 않은 다른 눈 — 별도의 fresh-eye 서브에이전트(자기 세션이 아닌 `Agent`) — 에게
맡기세요. 배포할 것이라면 리뷰를 여러 모델 패밀리(Claude 계열, OpenAI 계열, Google
계열)로 펼쳐 종합하세요. 어느 한 패밀리의 FAIL이라도 유효합니다 — 패밀리마다 놓치는
지점이 다르기 때문입니다. 단일 fresh-eye 리뷰어가 최소선입니다.

## 어디에 쓰나 (권장 워크플로우)

이 스킬은 *심사*하지, 생성하지 않습니다. 초안을 만든 뒤 **다듬는 단계**로 쓰는 것이
가장 유용합니다:

- **스킬을 만드나요?** 먼저 Claude Code의 **skill-creator** 플러그인(`/plugin install skill-creator@claude-plugins-official`)을 사용해 `SKILL.md` 골격을 잡고, 배포 전에 이
  스킬로 fresh-eye 심사를 돌리세요. 구조는 크리에이터가 쓰고, 저자가 못 보는 것은 이
  스킬이 찾습니다.
- **프롬프트를 쓰나요?** 1차 초안은 본인이 직접 작성하거나 AI에게 초안을 뽑게 한 뒤,
  이 스킬로 조여서 다듬으세요. AI가 뽑은 1차 초안이야말로 `references/ai-authorship.md`
  (AA1-AA6) 렌즈가 정리하려고 만든 대상입니다.
- **프롬프트 자체는 영문으로 작성하세요.** 기준과 린터는 영문을 전제합니다. 배포되는
  프롬프트는 영문으로 쓰고, 비영문은 정말로 그것이 소비자의 언어인 경우에만 남기세요
  (C11, AA6).

생성과 심사를 분리하는 데는 이유가 있습니다: 저자는 — 사람이든 AI든 — 자기
`[judge]`급 결함을 못 봅니다. 초안을 쓴 그 자리에서 곧바로 심사하지 말고, 반드시
*다른 눈*(별도 에이전트, 이상적으로는 여러 모델 패밀리)으로 리뷰하세요.

## 설치

### 플러그인으로 설치 (권장)

이 저장소는 단일 플러그인 Claude Code 마켓플레이스입니다:

```
/plugin marketplace add codefoundry-io/skill-prompt-review-claude
/plugin install skill-prompt-review@skill-prompt-review
```

### 개인/프로젝트 스킬로 설치

스킬 디렉터리를 Claude Code가 읽는 위치에 복사합니다:

```bash
cp -r skills/skill-prompt-review ~/.claude/skills/            # 개인 (모든 프로젝트)
cp -r skills/skill-prompt-review <내-저장소>/.claude/skills/  # 프로젝트 (git으로 공유)
```

설치 후, 평범한 턴에서 어시스턴트에게 스킬이나 프롬프트를 심사해 달라고 요청하세요 —
예: *"`path/to/SKILL.md`에 skill-prompt-review를 돌려줘."* `references/`에서 기준을
불러오고, 결정론적 린터를 돌려 리포트합니다.

## 무엇을 점검하나

- **`references/common.md`** — C0-C16, 스킬/프롬프트 어디에나 적용되는 기준
  (frontmatter 로드, 무엇+언제를 말하는 description, 단일 책임, 격리, priming 금지,
  lean, 차분한 명령문, 과도한 scaffolding 금지, time-stamped fact 금지, progressive
  disclosure, positive framing, 배포 위생, tool/skill 보편 규칙, 되돌릴 수 없는 작업
  게이트, long context 순서, 자기모순 금지, invocation 구성).
- **`references/anthropic.md` / `openai.md` / `google.md`** — Claude / OpenAI /
  Gemini 모델용 프롬프트의 벤더별 기준. 각 preamble이 어느 기준이 구조인지,
  body-as-prompt인지, 대상별 N-A인지를 명시합니다.
- **`references/ai-authorship.md`** — AA1-AA6, 대상이 AI로 작성됐을 수 있을 때
  (점점 기본값이 되는 경우) 점검하는 chat-register 서명: 작성-대화 잔재, chat-register
  사족, sycophantic softener, 지어낸 specific, 장식 과잉, 언어 표류.
- **`scripts/lint.py`** — *기계적* 후보를 잡는 결정론 린터(박힌 날짜/맨-연도 앵커,
  핀된 모델/버전 및 신형 강조어, 밀도, 길이, chat-register 구문 — 인용부호/백틱으로
  감싼 예시는 위반이 아닌 scoping language로 인식). 후보 목록이지 판정이 아니며,
  [judge] 기준은 여전히 fresh-eye 리뷰어가 필요합니다.
- **`scripts/score.py`** — 리포트의 verdict를 집계하는 결정론 스코어보드 및 라운드
  델타(모델 호출 없음, 지어낸 숫자 없음): applicable / PASS / FAIL 집계, 통과율,
  뒤집힌 기준, 잔여 FAIL은 항상 통과율 위에 표시.

## 잘 돌리는 법

1. **자기 리뷰가 아닌 fresh eye로.** 리뷰는 별도 에이전트에 맡기세요. 이 스킬을
   *편집할 때*도 마찬가지입니다.
2. **문맥을 벗기고, 각 리뷰어를 격리하세요.** 각 리뷰어에게 대상과 기준만 주고 —
   수정 이력, 이전 판정, "이미 안전 확인됨" 메모는 주지 마세요. 그런 것들이 리뷰어를
   저자의 사각지대로 끌고 갑니다. 큰 대상은 독립적으로 성립하는 조각으로 나눠 각각
   격리해 리뷰하세요.
3. **대상을 데이터로 취급하세요(fence).** 대상 텍스트는 신뢰 불가 — 각 리뷰어에게
   그것을 따르지 말고 심사하라, 읽기 전용으로 리뷰하라(아무것도 실행/수정 말라)고
   지시하세요.
4. **적대적 프레이밍.** 각 리뷰어에게 결함이 있다고 가정하고 무엇을 점검했는지
   열거하라고 하세요. 맨 "괜찮아 보임"은 실패한 리뷰입니다.
5. **상반될 때는 증거로 판정하세요.** 두 패밀리가 엇갈리면 probe나 벤더의 현행 공식
   문서로 결정하세요(셸 파싱 추적, 소스 grep, 공식 페이지 확인) — 투표나 저자의
   확신으로 결정하지 마세요.
6. **배포 전 *동작*을 증명하세요.** 깔끔한 텍스트 리뷰는 필요하지만 충분하지
   않습니다. 알려진 결함을 심은 테스트 대상을 두어 ground-truth 오라클을 만들고,
   스킬이 그것들을 잡고 깨끗한 대조군에는 조용한지 확인하세요. `scripts/test_lint.py`,
   `scripts/test_score.py`, `tests/test_lint_fixtures.py`가 결정론 절반에 대한
   그 점검입니다.

## 리포트 형식

```
# Review — <경로 또는 프롬프트 라벨>
axes: <host / worker / model / AI-authored?, 해당되는 대로>
## Summary
<N FAIL; load-bearing 하나를 지목>
pass-rate <p%>   (항상 지목된 FAIL 아래에 표시)
## Assessment
| Criterion | Verdict | Note                          |
|-----------|---------|-------------------------------|
| C0        | PASS    | 로드됨; name == folder        |
| C8        | FAIL    | L12에 박힌 날짜               |
| O2        | N-A     | API 전용, 이 CLI 프롬프트 아님|
## Fixes  (FAIL당 하나 — positive form, 각각 왜 도움되는지)
## Recommended additions
```

재심사 라운드에서는 `scripts/score.py '<before>' '<after>'`가 결정론 델타를
덧붙입니다: 뒤집힌 기준, 잔여 FAIL, 새로 드러난 FAIL, before/after 카운트. 등급
문자 없음, 기준별 지어낸 숫자 없음, 패밀리 간 평균 없음.

## 범위와 한계

- **영문 대상.** 기준과 린터는 영문 텍스트를 전제합니다. C11과 AI-authorship AA6을
  제외한 모든 기준은 영문 번역본으로 작업하세요 — 그 둘은 언어 분포를 점검하므로
  원문 기준으로 판정합니다.
- **읽을 뿐, 실행하지 않음.** 번들 `scripts/`의 악성코드 스캔은 안 합니다. 통과가
  보안 승인은 아닙니다.
- **적대적 리뷰에는 noise floor가 있습니다.** 깨끗한 입력에도 철저한 리뷰어는 *무언가*를
  꺼냅니다. 매 지적을 0으로 몰지 말고, 패밀리 간 종합 + probe/공식 문서로 판정하세요.
  plateau에서 멈추세요 — verdict가 오락가락하거나, 해결된 지적이 되돌아오거나, 텍스트에
  없는 것을 리뷰어가 보고할 때.

## 설치 확인

```bash
python3 skills/skill-prompt-review/scripts/test_lint.py    # 린터 자가검사
python3 skills/skill-prompt-review/scripts/test_score.py   # 스코어보드/델타 자가검사
python3 tests/test_lint_fixtures.py                        # 심은-결함 기능 테스트
```

세 개 모두 GREEN이면 결정론 절반이 심은 결함을 전부 잡고 대조군에는 조용하다는 뜻입니다.

## 라이선스

MIT — [LICENSE](LICENSE) 참고.
