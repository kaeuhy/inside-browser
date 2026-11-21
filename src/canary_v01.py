import socket
import os
import sys
import ssl
from dis import CACHE

def read_chunked(response):
    chunks = []
    while True:
        size_line = response.readline().decode("utf8").strip()
        chunk_size = int(size_line.split(";", 1)[0], 16)
        if chunk_size == 0:
            response.readline()
            break
        chunks.append(response.read(chunk_size))
        response.readline()
    return b"".join(chunks)


# URL 파싱
class URL:
    def __init__(self, url):
        # scheme 처리
        self.scheme, url = url.split("://", 1)
        # 실습 브라우저에서는 http만 사용 예정 + https 추가
        assert self.scheme in ["http", "https", "file"]

        # 암호화된 HTTP 연결은 443 포트를 사용
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if self.scheme == "file":
            if os.name == "nt" and url.startswith("/") and len(url) > 2 and url[2] == ":":
                url = url[1:]
            self.path = url
            return

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
    def request(self, redirects=5):
        if self.url in CACHE:
            body, expires_at = CAHE[self.url]
            if expires_at is None or time.time() < exxpires_at:
                return body
            del CACHE[self.url]

        assert redirects > 0, "Too many redirects"

        if self.scheme == "file":
            with open(self.path, encoding="utf8") as f:
                return f.read()

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
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
        # HTTP 1.1은 지속 연결이 기본값이기에 서버가 연결을 끊을 때까지 연결하려면 해당을 명시해야함
        request += "Connection: close\r\n"
        request += "User-Agent: my-browser/1.0\r\n"
        request += "Accept-Encoding: gzip\r\n"
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

        # Redirects
        if status in ["301", "302"]:
            location = response_headers["location"]
            if location.startswith("/"):
                location = "{}://{}:{}{}".format(
                    self.scheme, self.host, self.port, location
                )
            return URL(location).request(redirects - 1)

        # CACHE
        if status == "200" and "cache-control" in response_headers:
            cache_control = response_headers.get("cache-control", "")
            directives = [
                d.strip().lower() for d in cache_control.split(",") if d.strip()
            ]

            should_cache = True
            expires_at = None

            for d in directives:
                # 절대 캐시하지 않음
                if d == "no-store":
                    should_cache = False
                    break
                elif d.startswith("max-age="):
                    max_age = int(d.split("=", 1)[1])
                    expires_at = time.time() + max_age
                else:
                    should_cache = False
                    break
            if should_cache:
                CACHE[self.url] = (body, expires_at)

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
    target = sys.argv[1] if len(sys.argv) > 1 else "file:///path/to/default.html"
    load(URL(target))