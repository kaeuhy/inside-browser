# inside-browser

## 아키텍처

```mermaid
flowchart LR
    URL_IN(["URL 문자열"]) --> URL

    subgraph NET["네트워크"]
        URL["URL.request()<br/>소켓 + TLS, HTTP 요청"]
    end

    subgraph PARSE["텍스트 처리"]
        LEX["lex()<br/>태그 제거"]
        LAYOUT["layout()<br/>글자 위치 계산"]
    end

    subgraph UI["Browser (Tk)"]
        DL[("display_list<br/>(x, y, 글자)")]
        DRAW["draw()<br/>캔버스에 그리기"]
    end

    URL -- "HTML" --> LEX
    LEX -- "텍스트" --> LAYOUT
    LAYOUT -- "페이지 좌표" --> DL
    DL --> DRAW
    DRAW -- "y - scroll" --> SCREEN(["화면"])
```

- **layout은 한 번만 실행된다.** 결과(`display_list`)를 저장해 두고, 스크롤할 때는 `draw`만 다시 실행한다.
- **좌표계는 두 가지다.** 페이지 좌표(`layout`이 계산)에서 `self.scroll`을 빼면 화면 좌표(`draw`가 그림)가 된다.

<br/>
<br/>

## 실행 흐름

```mermaid
sequenceDiagram
    actor User as 사용자
    participant B as Browser
    participant U as URL
    participant S as 서버
    participant C as Canvas

    User->>B: python3 browser.py URL
    B->>U: request()
    U->>S: GET path HTTP/1.0
    S-->>U: 상태줄 + 헤더 + 본문
    U-->>B: HTML 본문
    B->>B: lex() → layout() → display_list 저장
    B->>C: draw()

    loop ↓ 키 입력마다
        User->>B: scrolldown()
        B->>B: scroll += 100
        B->>C: delete("all") 후 다시 그리기
    end
```
