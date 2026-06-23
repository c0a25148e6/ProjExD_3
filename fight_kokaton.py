import os
import random
import sys
import time
import pygame as pg
import math


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5 # 爆弾の数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
            self.dire = tuple(sum_mv)
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird:"Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load(f"fig/beam.png")
        self.rct = self.img.get_rect()
    
        self.vx, self.vy = bird.dire  # こうかとんの向きをビームの速度にする
        
        # 角度を計算して画像を回転させる
        angle = math.degrees(math.atan2(-self.vy, self.vx))  # y軸は下向きが正なのでマイナスをつける
        self.img = pg.transform.rotozoom(self.img, angle, 1.0)
        
        self.rct = self.img.get_rect()
        
        # こうかとんの中心から、向いている方向に少しずらした位置から発射
        self.rct.centerx = bird.rct.centerx + bird.rct.width * self.vx // 5
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy // 5
        # self.rct.centery = bird.rct.centery # こうかとんの中心座標
        # self.rct.left = bird.rct.right # こうかとんの右座標
        # self.vx, self.vy = +5, 0
        
    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)    


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)
        
        
class Score:
    """
    打ち落とした爆弾の数を表示するスコアクラス
    """
    def __init__(self):
        self.fonto = pg.font.Font(None, 50)  # フォントの設定
        self.color = (0, 0, 255)  # 文字色の設定：青
        self.score = 0  # スコアの初期値の設定：0
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)  # 画面左下に表示

    def update(self, screen: pg.Surface):
        """
        現在のスコアを表示させる文字列Surfaceの生成と描画
        """
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.img, self.rct)
        
        
class Explosion:
    """
    爆弾打ち落とし時の爆発エフェクトクラス
    """
    def __init__(self, bomb: Bomb, life: int):
        img = pg.image.load("fig/explosion.gif")
        # 元の画像と、上下左右反転させた画像の2つをリストに格納
        self.imgs = [img, pg.transform.flip(img, True, True)]
        self.rct = self.imgs[0].get_rect()
        self.rct.center = bomb.rct.center  # 爆発位置を爆弾がいた位置に設定
        self.life = life  # 爆発の表示時間

    def update(self, screen: pg.Surface):
        """
        爆発時間を減算し、交互に画像を切り替えて描画する
        """
        self.life -= 1
        if self.life > 0:
            # lifeの値を10で割った余りを使うことで、チラつきを抑えて画像を切り替える
            screen.blit(self.imgs[self.life // 10 % 2], self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    # bomb = Bomb((255, 0, 0), 10)
    # bombs = []
    # for _ in NUM_OF_BOMBS:
    #     bomb = Bomb((255, 0, 0), 10)
    #     bombs.append(bomb)
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    # beam = None  # ゲーム初期化時にはビームは存在しない
    beams = []
    score = Score() # scoreインスタンス作成
    exps = []
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                # beam = Beam(bird)    
                beams.append(Beam(bird)) # beamをリストに追加     
        screen.blit(bg_img, [0, 0])
        
# こうかとんと爆弾の衝突判定
        for bomb in bombs:
            if bomb is not None:
                if bird.rct.colliderect(bomb.rct):
                    bird.change_img(8, screen)
                    fonto = pg.font.Font(None, 80)
                    txt = fonto.render("Game Over", True, (255, 0, 0))
                    screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                    pg.display.update()
                    time.sleep(1) 
                    return
        
        # 爆弾とビームの衝突判定
        for i, bomb in enumerate(bombs): # enumerateを使ってインデックス(i)を取得
            for j,beam in enumerate(beams):
                if bomb is not None and beam is not None:
                    if beam.rct.colliderect(bomb.rct):
                        exps.append(Explosion(bomb, 50))
                        beams[j] = None # 当たったbeamをNoneにする
                        bombs[i] = None # 当たった爆弾をNoneにする
                        bird.change_img(6, screen) # こうかとんが喜ぶ
                        score.score += 1 # score追加

        # Noneになった（撃ち落とされた）爆弾をリストから取り除く
        bombs = [bomb for bomb in bombs if bomb is not None]
        
        # Noneになったビームと、画面外に出たビームをリストから取り除く
        beams = [beam for beam in beams if beam is not None]
        beams = [beam for beam in beams if check_bound(beam.rct) == (True, True)]
        
        # lifeが0より大きい（まだ爆発中の）エフェクトだけを残す
        exps = [exp for exp in exps if exp.life > 0]

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
            
        # ビームの描画（リスト内のすべてのビームをupdateする）
        for beam in beams:
            beam.update(screen)
            
        # 爆弾の描画（リストに残っている爆弾をすべてupdateする）
        for bomb in bombs:
            bomb.update(screen)
            
        # 爆発エフェクトの描画（score.update(screen) の直前あたり）
        for exp in exps:
            exp.update(screen)
        score.update(screen) # scoreを画面に表示
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
