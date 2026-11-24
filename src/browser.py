import socket
import sys
import ssl
import tkinter
import tkinter.font

# 네트워크 계층
class URL:
    def __init__(self, url):
        # 1. 프로토콜(scheme) 분리
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https"]

        # 2. 프로토콜별 기본 포트 번호 설정
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        # 3. 도메인(host), 경로(path) 분리
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        # 사용자 지정 포트가 있으면 기본 포트를 덮어씀
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)


    # 실제 서버 접속 및 HTTP 요청/응답 처리 (OS 소켓 + 원격 서버 통신)
    # 반환값은 HTTP 헤더를 제거한 순수 HTML 본문 문자열
    def request(self):
        # AF_INET: IPv4 주소 체계 사용 (예: 93.184.216.34)
        # SOCK_STREAM: 데이터가 유실되거나 순서가 바뀌지 않는 스트림 방식
        # IPPROTO_TCP: 전송 규약으로 TCP 프로토콜 사용
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )

        # OS 커널이 대신 TCP 3-way handshake(SYN → SYN-ACK → ACK)를 수행해 서버와 연결
        s.connect((self.host, self.port))

        # https인 경우 기존 TCP 소켓을 SSL 암호화 소켓으로 감싸기
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # 서버에 요청을 보내는 단계로 send 메서드를 사용
        request = "GET {} HTTP/1.0\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
        request += "\r\n"
        s.send(request.encode("utf8"))

        # 서버의 응답을 읽으려면 이미 도착한 응답을 전달하는 소켓의 read 메서드를 사용
        # makefile을 사용하여 서버로부터 받은 모든 바이트가 포함된 파일 형식의 객체를 반환
        response = s.makefile("r", encoding="utf8", newline="\r\n")

        # 응답을 나누어 처리
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        # 응답 헤더 파싱
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        body = response.read()
        s.close()

        return body

# HTML 태그를 제외하고 본문 텍스트만 출력
def lex(body):
    text = ""
    # 처리 중인 글자가 부등호 안에 있으면 true
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    return  text

WIDTH, HEIGHT = 800, 600
# 기본 가로, 세로 여백
HSTEP, VSTEP = 13, 18
# 아래 방향키  한 번당 스크롤 이동 픽셀
SCROLL_STEP = 100

def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    font = tkinter.font.Font()

    # 단어 단위로 좌표를 계산
    for word in text.split():
        w = font.measure(word)
        if cursor_x + w > WIDTH - HSTEP:
            cursor_y += font.metrics("linespace") * 1.25
            cursor_x = HSTEP
        display_list.append((cursor_x, cursor_y, word))
        cursor_x += w + font.measure(" ")

    # 글자 단위로 좌표를 계산
    # for c in text:
    #     display_list.append((cursor_x, cursor_y, c))
    #     cursor_x += HSTEP
    #
    #     if cursor_x >= WIDTH - HSTEP:
    #         cursor_y += VSTEP
    #         cursor_x = HSTEP

    return display_list

# 브라우저 코어
class Browser:
    def __init__(self):
        # tkinter.Tk() 객체는 데스크톱 환경에 창을 만들도록 요청하고 무언가를 그리는데 사용할 객체를 반환
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()

        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)

    # 웹 페이지 요청 및 출력 실행
    def load(self, url):
        body = url.request()
        text = lex(body)
        self.display_list = layout(text)
        self.draw()

    # 디스플레이 리스트를 화면 좌표계로 변환해 그리기
    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

# 직접 실행 시 진입점
if __name__ == "__main__":
    Browser().load(URL(sys.argv[1]))
    # mainloop()를 호출하면 pendingEvent, handleEvent, drawScreen 루프가 돌아감
    tkinter.mainloop()