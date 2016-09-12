'''
TabbedPanel
============

Test of the widget TabbedPanel.
'''
import sys
import os
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.scrollview import ScrollView
from animlabel import AnimLabel

Builder.load_string("""
# Elite Orange: #ff7100
# Horizons: #0a8bd6
# Felicity: #ff7f00
# Alliance: #029e4c
# Independant: #ffb000
# Empire: #00b3f7 - THE blue colour
# Denton: #00ffff
# Federation: #ff0000
# Mahun: #00ff00
# From: http://edassets.org
<RootWidget>:   # which is a BoxLayout
    orientation: 'vertical'
    background_normal: ''
    background_color: ( 0, 0, 0, 0 )
    border: ( 0, 0, 0, 0 )
    canvas.before:
        Color:
            rgba: 1, 0.48, 0, 1
        BorderImage:
            # BorderImage behaves like the CSS BorderImage
            border: 10, 10, 10, 10
            source: 'assets/images/test.jpg'
            pos: self.pos
            size: self.size

    TabbedPanel:
        size_hint: (1, 0.7)
        tab_width: 200
        do_default_tab: False
        TabbedPanelItem:
            background_normal: 'assets/images/button-inactive.png'
            background_down: 'assets/images/button-down.png'
            # background_color: (1, 0.52, 0, 1)
            canvas.before:
                Color:
                    rgba: 1, 0.48, 0, 1
                BorderImage:
                    # BorderImage behaves like the CSS BorderImage
                    border: 10, 10, 10, 10
                    source: 'assets/images/test.jpg'
                    pos: self.pos
                    size: self.size
            markup: 'true'
            text: '[color=#000000][size=24]STATUS[/size][/color]'
            font_name: 'assets/fonts/EUROCAPS'
            BoxLayout: # Root Box for Layout of Tab 1 (provides color for borders)
                canvas.before:
                    Color:
                        rgba: 1, 0.48, 0, 1
                    Rectangle:
                        # self here refers to the widget i.e FloatLayout
                        pos: self.pos
                        size: self.size
                orientation: 'vertical'
                spacing: 1

                BoxLayout:  # This is the container for top two panels
                    size_hint: (1, 1)
                    orientation: 'horizontal'
                    padding: 1
                    spacing: 1
                    BoxLayout:  # Container for left hand panel
                        canvas.before:
                            Color:
                                rgba: 1, 0.48, 0, 1
                            BorderImage:
                                # BorderImage behaves like the CSS BorderImage
                                border: 10, 10, 10, 10
                                source: 'assets/images/test.jpg'
                                pos: self.pos
                                size: self.size
                        orientation: 'vertical'
                        padding: 5
                        spacing: 1
                        Label:
                            size_hint: (1, 0.06)
                            font_name: 'assets/fonts/MICROGME.ttf'
                            markup: 'true'
                            halign: 'left'
                            valign: 'middle'
                            text_size: self.size
                            font_size: 14
                            text: '[color=#ff7100]CMDR[/color]  [color=#ffb000]UNKNOWN COMMANDER[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba:  1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            padding: 4
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ffb000]COMBAT  UNKNOWN[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ffffff]TRADE  UNKNOWN[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            padding: 4
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#0a8bd6]EXPLORE  UNKNOWN[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff0000]CQC  UNKNOWN[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            padding: 4
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]FEDERATION REP[/color]  [color=#ffb000]FRIENDLY[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#00b3f7]EMPIRE REP[/color]  [color=#ffb000]FRIENDLY[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            padding: 4
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]FEDERATION RANK[/color]  [color=#ffb000]PETTY OFFICER[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#00b3f7]EMPIRE RANK[/color]  [color=#ffb000]SQUIRE[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            padding: 4
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#029e4c]ALLIANCE REP[/color]  [color=#ffb000]NEUTRAL[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#00ff00]THARGOID REP[/color]  [color=#ffb000]NEUTRAL[/color]'
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint: (1, 0.06)
                            padding: 0
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 14
                                text: '[color=#ff7100]SHIP[/color]  [color=#ffb000]MARIE-CELESTE[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 14
                                text: '[color=#ff7100]SHIP TYPE[/color]  [color=#ffb000]Cobra MkIV[/color]'
                        Label:
                            size_hint: (1, 0.06)
                            font_name: 'assets/fonts/MICROGME.ttf'
                            markup: 'true'
                            halign: 'left'
                            valign: 'middle'
                            text_size: self.size
                            font_size: 14
                            text: '[color=#ff7100]CREDITS[/color]  [color=#ffb000]123,456,45 CR[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            padding: 4
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]INSURANCE[/color]  [color=#ffb000]4,567,789 CR[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]LOCAL BOUNTY[/color]  [color=#ffb000]12,345 CR[/color]'
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint: (1, 0.06)
                            padding: 0
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 14
                                text: '[color=#ff7100]LOCATION[/color]  [color=#ffb000]DOCKED[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 14
                                text: '[color=#ff7100]LOCAL REP[/color]  [color=#ffb000]NEUTRAL[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            padding: 4
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]SYSTEM[/color]  [color=#ffb000]LAVE[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]ALLEGIENCE[/color]  [color=#ff7100]FEDERATION[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            padding: 4
                            spacing: 0
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]FACTION[/color]  [color=#ffb000]Coalition of Paitina[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]STATE[/color]  [color=#ffb000]Civil War[/color]'

                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            padding: 4
                            spacing: 0
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]ECONOMY[/color]  [color=#ffb000]Agriculture[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]GOV[/color]  [color=#ffb000]DICTATORSHIP[/color]'

                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            padding: 4
                            spacing: 0
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]BODY/STATION[/color]  [color=#ffb000]Lave Station[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]PAD[/color]  [color=#ffb000]28[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            padding: 4
                            spacing: 0
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]FACTION[/color]  [color=#ffb000]Coalition of Paitina[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]SECURITY[/color]  [color=#ffb000]High Security[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            padding: 4
                            spacing: 0
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]ECONOMY[/color]  [color=#ffb000]Agriculture[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]GOV[/color]  [color=#ffb000]DICTATORSHIP[/color]'

                        Label:
                            size_hint: (1, 0.06)
                            font_name: 'assets/fonts/MICROGME.ttf'
                            markup: 'true'
                            halign: 'left'
                            valign: 'middle'
                            text_size: self.size
                            font_size: 14
                            text: '[color=#ff7100]MISSIONS[/color]  [color=#ffb000]1[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            padding: 4
                            spacing: 0
                            Label:
                                size_hint: (0.3, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ffb000]Bunda Bridge & Co[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ffb000]Delivery[/color]'
                            Label:
                                size_hint: (0.2, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'right'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ffb000]6d 4h 3m[/color]'

                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint: (1, 0.06)
                            padding: 0
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 14
                                text: '[color=#ff7100]CARGO[/color]  [color=#ffb000]10/32[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 14
                                text: '[color=#ff7100]VALUE[/color]  [color=#ffb000]102,384 CR[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            padding: 4
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]Fish[/color]  [color=#ffb000]5[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]Atmospheric Processors[/color]  [color=#ffb000]2[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            padding: 4
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]Lavian Brandy[/color]  [color=#ffb000]1[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]Unidentied Artifact[/color]  [color=#ffb000]1[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            padding: 4
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]Lavian Brandy[/color]  [color=#ffb000]1[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]Unidentied Artifact[/color]  [color=#ffb000]1[/color]'
                        BoxLayout:
                            canvas.before:
                                Color:
                                    rgba: 1, 0.52, 0, 0.1
                                Rectangle:
                                    # self here refers to the widget i.e FloatLayout
                                    pos: self.pos
                                    size: self.size
                            orientation: 'horizontal'
                            size_hint: (1, 0.05)
                            padding: 4
                            spacing: 0
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]Lavian Brandy[/color]  [color=#ffb000]1[/color]'
                            Label:
                                size_hint: (0.5, 1)
                                font_name: 'assets/fonts/MICROGME.ttf'
                                markup: 'true'
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                                font_size: 12
                                text: '[color=#ff7100]Unidentied Artifact[/color]  [color=#ffb000]1[/color]'

                    BoxLayout:  # Container for right hand HUD panel
                        canvas.before:
                            Color:
                                rgba: 1, 0.48, 0, 1
                            BorderImage:
                                # BorderImage behaves like the CSS BorderImage
                                border: 10, 10, 10, 10
                                source: 'assets/images/test.jpg'
                                pos: self.pos
                                size: self.size
                        orientation: 'vertical'
                        padding: 5
                        spacing: 1
                        Label: # Contextual Data Container maybe should be ScrollView
                            size_hint: (1, 0.7)
                            font_name: 'assets/fonts/MICROGME.ttf'
                            markup: 'true'
                            halign: 'left'
                            valign: 'top'
                            text_size: self.size
                            text:
                                '\\n'.join(("[color=#ffffff]CONTEXTUAL DATA FEED[/color]",
                                "-------------------------------------------------------",
                                "[color=#ffb000]consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.[/color]",
                                "[color=#00ffff]DUIS ARETE irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.[/color]"))

        TabbedPanelItem:
            background_normal: 'assets/images/button-inactive.png'
            background_down: 'assets/images/button-down.png'
            #background_color: (0, 0, 0, 0)
            markup: 'true'
            text: '[color=#000000][size=24]JOURNAL[/size][/color]'
            font_name: 'assets/fonts/EUROCAPS'
            BoxLayout:
                orientation: 'vertical'
                BoxLayout:
                    size_hint: (1, 0.7)
                    Label:
                        text_size: self.size
                        halign: 'center'
                        valign: 'middle'
                        font_name: 'assets/fonts/telegrama_render.otf'
                        markup: 'true'
                        text:
                            '\\n'.join(("[color=#ffffff]LOREM IPSUM DOLOR SIT AMET[/color]",
                            "-------------------------------------------------------",
                            "[color=#ffb000]consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.[/color]",
                            "[color=#00ffff]DUIS ARETE irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.[/color]"))
                    Button:
                        text_size: self.size
                        halign: 'center'
                        valign: 'middle'
                        font_name: 'assets/fonts/Sintony-Regular.ttf'
                        background_color: (0, 0, 0, 0)
                        markup: 'true'
                        text: '[color=#ff7100]Button that does nothing[/color]'
                    Button:
                        text_size: self.size
                        halign: 'center'
                        valign: 'middle'
                        font_name: 'assets/fonts/Sintony-Regular.ttf'
                        background_normal: ''
                        background_color: (1, 0.52, 0, 1)
                        markup: 'true'
                        text: '[color=#000000]Button that does nothing[/color]'
                ListView:
                    size_hint: (1, 0.3)
                    ListItemButton:
                        text: "Button01"
                        size_hint_y: None
                        height: 25
                    ListItemButton:
                        text: "Button02"
                        size_hint_y: None
                        height: 25
                    ListItemButton:
                        text: "Button03"
                        size_hint_y: None
                        height: 25
                    ListItemButton:
                        text: "Button04"
                        size_hint_y: None
                        height: 25

        TabbedPanelItem:
            background_normal: 'assets/images/button-inactive.png'
            background_down: 'assets/images/button-down.png'
            #background_color: (0, 0, 0, 0)
            markup: 'true'
            text: '[color=#000000][size=24]LOADOUT[/size][/color]'
            font_name: 'assets/fonts/EUROCAPS'
            RstDocument:
                background_color: (0, 0, 0, 0)
                font_name: 'assets/fonts/Sintony-Regular.ttf'
                text:
                    '\\n'.join(("Hello world", "-----------",
                    "You are in the third tab."))

    BoxLayout:  # This is the container for the bottom two panels
        size_hint: (1, 0.3)
        canvas.before:
            Color:
                rgba: 1, 0.48, 0, 1
            BorderImage:
                # BorderImage behaves like the CSS BorderImage
                border: 10, 10, 10, 10
                source: 'assets/images/test.jpg'
                pos: self.pos
                size: self.size
        padding: 0
        spacing: 5
        orientation: 'horizontal'
        BoxLayout:  # Frame only to hold terminal unit border
            canvas.before:
                Color:
                    rgba: 1, 0.48, 0, 1
                BorderImage:
                    # BorderImage behaves like the CSS BorderImage
                    border: 10, 10, 10, 10
                    source: 'assets/images/black-frame-cropped.png'
                    pos: self.pos
                    size: self.size
            size_hint: (0.5, 1)
            padding: ( (self.width/11), (self.height/7) )
            ScrollView:
                size_hint: (1, 1)
                Label:
                    size_hint: (1, None)
                    text_size: self.width, None
                    size: self.texture_size
                    font_name: 'assets/fonts/EUROCAPS.ttf'
                    markup: 'true'
                    halign: 'left'
                    valign: 'top'
                    text: '[color=#ff7100]Lorem ipsum dolor sit amet, consectetur adipiscing elit,[/color][color=#ffb000] sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.[color=#ff7100]Lorem ipsum dolor sit amet, consectetur adipiscing elit,[/color][color=#ffb000] sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.[color=#ff7100]Lorem ipsum dolor sit amet, consectetur adipiscing elit,[/color][color=#ffb000] sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.[/color][color=#ff7100]Lorem ipsum dolor sit amet, consectetur adipiscing elit,[/color][color=#ffb000] sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.[color=#ff7100]Lorem ipsum dolor sit amet, consectetur adipiscing elit,[/color][color=#ffb000] sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.[color=#ff7100]Lorem ipsum dolor sit amet, consectetur adipiscing elit,[/color][color=#ffb000] sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.[/color]'
        BoxLayout:  # Container for Functional Controls
            orientation: 'vertical'
            size_hint: (0.5, 1)
            # Functional Control 4 x 3
            BoxLayout:  # Row 1
                orientation: 'horizontal'
                size_hint: (1, 0.33)
                Button:
                    background_normal: 'assets/images/button-inactive.png'
                    background_down: 'assets/images/button-inactive-down.png'
                    size_hint: (0.125, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'UNUSED'
                Button:
                    background_normal: 'assets/images/button.png'
                    background_down: 'assets/images/button-down.png'
                    size_hint: (0.125, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'UP'
                Button:
                    background_normal: 'assets/images/button-blue.png'
                    background_down: 'assets/images/button-blue-down.png'
                    size_hint: (0.25, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    halign: 'center'
                    text: 'TWO\\nLINES'

                Button:
                    background_normal: 'assets/images/button-inactive.png'
                    background_down: 'assets/images/button-inactive-down.png'
                    size_hint: (0.25, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'UNUSED'

                Button:
                    background_normal: 'assets/images/button-green-108.png'
                    background_down: 'assets/images/button-green-108-down.png'
                    size_hint: (0.25, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'RELOAD'
                    on_press: root.restart_program()

            BoxLayout:      # Row 2
                orientation: 'horizontal'
                size_hint: (1, 0.33)
                Button:
                    background_normal: 'assets/images/button.png'
                    background_down: 'assets/images/button-down.png'
                    size_hint: (0.125, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'LEFT'
                Button:
                    background_normal: 'assets/images/button.png'
                    background_down: 'assets/images/button-down.png'
                    size_hint: (0.125, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'SELECT'
                Button:
                    background_normal: 'assets/images/button.png'
                    background_down: 'assets/images/button-down.png'
                    size_hint: (0.125, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'RIGHT'
                Button:
                    background_normal: 'assets/images/button-inactive.png'
                    background_down: 'assets/images/button-inactive-down.png'
                    size_hint: (0.125, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'UNUSED'

                Button:
                    background_normal: 'assets/images/button-inactive.png'
                    background_down: 'assets/images/button-inactive-down.png'
                    size_hint: (0.25, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'UNUSED'

                Button:
                    background_normal: 'assets/images/button.png'
                    background_down: 'assets/images/button-down.png'
                    size_hint: (0.25, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'SUSPEND'


            BoxLayout:  # Row 3
                orientation: 'horizontal'
                size_hint: (1, 0.33)
                Button:
                    background_normal: 'assets/images/button-inactive.png'
                    background_down: 'assets/images/button-inactive-down.png'
                    size_hint: (0.125, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'UNUSED'
                Button:
                    background_normal: 'assets/images/button.png'
                    background_down: 'assets/images/button-down.png'
                    size_hint: (0.125, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'DOWN'

                Button:
                    background_normal: 'assets/images/button-inactive.png'
                    background_down: 'assets/images/button-inactive-down.png'
                    size_hint: (0.25, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'UNUSED'

                Button:
                    background_normal: 'assets/images/button-blue.png'
                    background_down: 'assets/images/button-blue-down.png'
                    size_hint: (0.25, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'DISPLAY MODE'
                    on_press: root.togglescreenmode()

                Button:
                    background_normal: 'assets/images/button-red.png'
                    background_down: 'assets/images/button-red-down.png'
                    size_hint: (0.25, 1)
                    font_name: 'assets/fonts/EUROCAPS'
                    text: 'SHUTDOWN'
                    on_press: exit()

""")






class RootWidget(BoxLayout):

    def restart_program(self):
            """Restarts the current program.
            Note: this function does not return. Any cleanup action (like
            saving data) must be done before calling this function."""
            python = sys.executable
            os.execl(python, python, * sys.argv)
            exit()

    def togglescreenmode(self):
        if (Window.fullscreen):
            Window.fullscreen = False
            Window.size = (1366, 768)
        else:
            Window.fullscreen = 'auto'

    Window.size = (1366, 768)


class MainApp(App):

    def build(self):
        return RootWidget()




if __name__ == '__main__':
    MainApp().run()
