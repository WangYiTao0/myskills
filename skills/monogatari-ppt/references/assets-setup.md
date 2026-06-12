# 资产获取与字库实测(不随 skill 分发)

模板字体栈带系统回退,缺资产时降级可用;要完整还原观感需自备以下文件,
放到与 deck HTML 同级的 `assets/` 目录(**勿提交进公开仓库**,均为受版权资产):

来源:物语风格文字生成器·第七代 <http://m.webcats.cn/bx/108332/62669/>

| 文件 | 源相对路径 | 用途 |
|---|---|---|
| HGPMinchoB.woff | `fonts/HGPMinchoB.woff` | 汉字/假名主字体(动画同款明朝体,Ricoh 商用) |
| MonotypeCorsiva.woff | `fonts/MonotypeCorsiva.woff` | 罗马字注音/页码(Monotype 商用) |
| BakemonogatariStyle.png | `background/BakemonogatariStyle.png` | 横纹纸+斑点纹理(黒齣/赤齣卡) |
| BakemonogatariSetting.png | `background/BakemonogatariSetting.png` | 柔棉纸纹理(設定集白卡) |

纹理用法:黑底 `mix-blend-mode:screen` 浓度 ~0.22;浅底 `multiply` ~0.4–0.55。

## 许可

HGP明朝B(Ricoh,随日文版 MS Office 分发)与 Monotype Corsiva 均为商用字体:
仅本机渲染使用;对外分发的课件包不得携带字体文件(字体栈回退已配好)。
《物语系列》动画原片画面为版权素材,模板中一律按"用户自备素材槽位"处理。

## 卡面文字字库实测(JIS 字库缺中文常用字)

上卡文字(走 HGPMinchoB 的显示层)先实测,缺字会回退成系统字体当场破功:

```bash
pip3 install --user --break-system-packages fonttools
python3 -c "from fontTools.ttLib import TTFont; cmap=TTFont('assets/HGPMinchoB.woff').getBestCmap(); print([c for c in '<待测文字>' if ord(c) not in cmap])"
```

已测结果:
- **缺**:你 们 說(用 説) 诊(用 診) 歷(用 歴) 设
- **有**:閒 齣 籠 它 們 説 診 歴 會 與 點 終 樣 號 畫 藝 壹 貳 參 差 十 倍

正文层(简体,走 Hiragino/Songti 栈)不受此限。
