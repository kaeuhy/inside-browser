import socket
import sys
import ssl

# URL 파싱
class URL:
    def __init__(self, url):
        # scheme 처리
        self.scheme, url = url.split("://", 1)
        # 실습 브라우저에서는 http만 사용 예정 + https 추가
        assert self.scheme in ["http", "https"]

        # 암호화된 HTTP 연결은 443 포트를 사용
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        # host, path 분리
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        # 사용자 지정 포트가 있으면 기본 포트를 덮어씀
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)


    # 다른 컴퓨터와 통신하기 위해 OS에서는 소켓이라는 기능을 제공함
    # 소켓 통신을 하기 위해 다음과 같은 요소를 사용
    def request(self):
        # family: 어떤 종류의 주소를 사용할지, AF_INET는 접속할 떄 주소를 IPv4 주소와 포틀 지정
        # type: 데이터를 주고받는 방식
        # proto: 사용할 통신 규칙
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )

        # 연결 지시
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
def show(body):
    # 처리 중인 글자가 부등호 안에 있으면 true
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

# 웹 페이지 요청 및 출력 실암
def load(url):
    body = url.request()
    show(body)

# 직접 실행 시 진입점
if __name__ == "__main__":
    load(URL(sys.argv[1]))