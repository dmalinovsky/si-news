Tracks updates for zhurnal.lib.ru authors. 

Useful for Russians only. Written on Python with PyQt.

Requirements: [python-pyquery](http://packages.python.org/pyquery/),
[python-qt4](http://www.riverbankcomputing.com/software/pyqt/download)

## Инструкция по-русски ##

Программа помогает следить за новинками СИ. После первого запуска нужно зайди в
меню "Файл/Параметры" и указать свою страничку друзей
([пример](http://zhurnal.lib.ru/cgi-bin/frlist?DIR=m/malinowskij_d)). После
этого нужно обновить список известных произведений с помощью меню
"Просмотр/Обновить". Теперь программа будет знать, какие произведения считать
старыми, и при последущих обновлениях отобразит новинки. Новым считается
произведение, добавленное или изменённое между обновлениями списка известных.
