Tracks updates for zhurnal.lib.ru (aka samlib.ru) authors. 

Useful for Russians only. Written on Python with Qt (PySide).

Requirements: [python-pyquery](http://packages.python.org/pyquery/),
[python-pyside](http://www.pyside.org/)

## Инструкция по-русски ##

Программа помогает следить за новинками [СИ](http://samlib.ru/).

Для установки можно использовать `pip install si-news`. Необходима версия
Python >= 2.6. PySide нужно установить вручную (для Debian/Ubuntu с помощью команды `apt-get install python-pyside`). Для запуска программы теперь можно использовать просто `si_news`.

После первого запуска нужно зайди в меню "Файл/Параметры" и указать свою страничку друзей ([пример](http://samlib.ru/cgi-bin/frlist?DIR=m/malinowskij_d)). После этого нужно обновить список известных произведений с помощью меню "Просмотр/Обновить". Теперь программа будет знать, какие произведения считать старыми, и при последущих обновлениях отобразит новинки. Новым считается произведение, добавленное или изменённое между обновлениями списка известных.

![Скриншот](https://lh5.googleusercontent.com/_5s5fpajuq2M/TXzlPQe3qII/AAAAAAAAEaM/uLMXjk1l_6c/s400/si-news.png)
