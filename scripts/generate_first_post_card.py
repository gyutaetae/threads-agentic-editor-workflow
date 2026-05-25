from PIL import Image, ImageDraw, ImageFont


WIDTH = 1080
HEIGHT = 1350
OUT = "threads-first-post-card.png"

FONT = r"C:\Windows\Fonts\malgun.ttf"
FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def multiline(draw, xy, text, fnt, fill, spacing=10):
    draw.multiline_text(xy, text, font=fnt, fill=fill, spacing=spacing)


def main():
    bg = (246, 247, 249)
    card = (255, 255, 255)
    ink = (18, 23, 31)
    muted = (96, 103, 115)
    line = (217, 222, 231)
    green = (15, 118, 110)
    red = (180, 35, 24)
    soft_green = (232, 250, 246)
    soft_red = (254, 243, 242)

    img = Image.new("RGB", (WIDTH, HEIGHT), bg)
    draw = ImageDraw.Draw(img)

    rounded(draw, (60, 60, 1020, 1290), 30, card, line, 3)

    draw.text((110, 120), "프로 개발자의", font=font(54, True), fill=ink)
    draw.text((110, 190), "AI agent 작업법", font=font(54, True), fill=green)
    multiline(draw, (112, 285), "잘 쓰는 사람은 프롬프트보다\n일을 잘게 쪼갠다", font(30), muted, 8)

    rounded(draw, (110, 410, 970, 650), 24, soft_red)
    draw.text((150, 445), "나쁜 요청", font=font(28, True), fill=red)
    draw.text((150, 505), '"앱 하나 만들어줘"', font=font(40, True), fill=ink)
    draw.text((150, 590), "범위가 너무 넓어서 agent도 사람도 헤맨다", font=font(24), fill=muted)

    rounded(draw, (110, 700, 970, 1080), 24, soft_green)
    draw.text((150, 735), "좋은 요청", font=font(28, True), fill=green)
    good = "1. failing test 하나만 고쳐줘\n2. PR에서 위험한 변경만 찾아줘\n3. 함수 타입 오류만 정리해줘"
    multiline(draw, (150, 800), good, font(35, True), ink, 16)
    multiline(draw, (150, 1010), "검증 가능한 작은 티켓으로 쪼개면\nAI agent가 훨씬 잘 작동한다", font(24), muted, 8)

    draw.line((110, 1135, 970, 1135), fill=line, width=2)
    multiline(draw, (110, 1165), "AI agent 시대의 실력 =\n명령어가 아니라 작업 분해", font(29, True), ink, 6)
    draw.text((110, 1240), "@gyu_in_black · AI agent 작업노트", font=font(23), fill=muted)

    img.save(OUT, quality=95)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
