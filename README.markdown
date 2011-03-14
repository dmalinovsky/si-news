Tracks updates for zhurnal.lib.ru authors. 

Useful for Russians only. Written on Python with PyQt.

Requirements: [python-pyquery](http://packages.python.org/pyquery/),
[python-qt4](http://www.riverbankcomputing.com/software/pyqt/download)

## Инструкция по-русски ##

Программа помогает следить за новинками СИ.

Для установки можно использовать `pip install si-news`. Необходима версия
Python >= 2.6. PyQt
нужно установить вручную (для Debian/Ubuntu с помощью команды `apt-get
install python-qt4`). Для запуска программы теперь можно использовать просто
`si_news`.

После первого запуска нужно зайди в
меню "Файл/Параметры" и указать свою страничку друзей
([пример](http://zhurnal.lib.ru/cgi-bin/frlist?DIR=m/malinowskij_d)). После
этого нужно обновить список известных произведений с помощью меню
"Просмотр/Обновить". Теперь программа будет знать, какие произведения считать
старыми, и при последущих обновлениях отобразит новинки. Новым считается
произведение, добавленное или изменённое между обновлениями списка известных.

<table style="width:auto;"><tr><td><a
href="https://picasaweb.google.com/lh/photo/QpL555__YA95vbxvl4N1GmSUucKC4aHYCggfktrfSac?feat=embedwebsite"><img
src="https://lh5.googleusercontent.com/_5s5fpajuq2M/TXzlPQe3qII/AAAAAAAAEaM/uLMXjk1l_6c/s400/si-news.png"
height="281" width="400" /></a></td></tr></table>
