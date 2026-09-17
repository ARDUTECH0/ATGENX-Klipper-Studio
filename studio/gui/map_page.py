# -*- coding: utf-8 -*-
"""Wiring map: the board in the middle, every device around it, and the pin each one uses."""
import os

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QFileDialog, QFormLayout, QFrame, QGraphicsItem, QGraphicsPathItem, QGraphicsScene,
                               QGraphicsSimpleTextItem, QGraphicsView, QHBoxLayout, QLabel, QLineEdit, QMenu,
                               QPushButton, QToolButton, QVBoxLayout, QWidget)

from .. import APP_NAME
from ..features import CATALOG, set_feature
from ..i18n import tr
from ..model import MOTOR_LABEL, OPTIONAL_MOTORS, PRIMARY
from ..wiring import set_pin, wiring

GROUP_COLOR = {"motors": "#58a6ff", "heat": "#ff7b54", "fans": "#4ad7d4", "sensors": "#d2a8ff",
               "lights": "#3fb950", "other": "#c9a227"}
NODE_W, LINE_H = 250, 15
SIDE = {"motors": "left", "heat": "top", "fans": "right", "lights": "right", "sensors": "bottom", "other": "bottom"}


class NodeItem(QGraphicsItem):
    def __init__(self, node, on_click):
        super().__init__()
        self.node = node
        self.on_click = on_click
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.hover = False
        self.edges = []
        self._h = 40 + LINE_H * max(1, len(node["pins"])) + (14 if node["note"] else 0)

    def boundingRect(self):
        return QRectF(0, 0, NODE_W, self._h)

    def paint(self, p, _opt, _widget=None):
        n = self.node
        color = QColor(GROUP_COLOR.get(n["group"], "#8b949e"))
        bad = bool(n["issues"])
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor("#161b22" if not n["off"] else "#12161d")))
        pen = QPen(QColor("#f85149") if bad else (color if (self.isSelected() or self.hover) else QColor("#2b3441")))
        pen.setWidth(2 if (bad or self.isSelected() or self.hover) else 1)
        if n["off"]:
            pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        p.drawRoundedRect(self.boundingRect().adjusted(1, 1, -1, -1), 10, 10)
        p.setPen(QColor("#e6edf3") if not n["off"] else QColor("#6e7681"))
        f = QFont("Segoe UI", 10)
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(12, 8, NODE_W - 24, 20), Qt.AlignLeft | Qt.AlignVCenter, "%s  %s" % (n["icon"], n["label"]))
        y = 30
        if n["note"]:
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor("#8b949e"))
            p.drawText(QRectF(12, y, NODE_W - 24, 14), Qt.AlignLeft, n["note"] + (("  ·  " + tr("map.off")) if n["off"] else ""))
            y += 14
        p.setFont(QFont("Consolas", 8))
        for pin in n["pins"]:
            p.setPen(QColor("#f85149") if pin.get("issue") else QColor("#b7c3d1"))
            text = "%s: %s" % (pin["label"], pin["pin"] or "—")
            p.drawText(QRectF(12, y, NODE_W - 24, LINE_H), Qt.AlignLeft | Qt.AlignVCenter, text)
            y += LINE_H

    def anchor(self, side):
        r = self.sceneBoundingRect()
        return {"left": QPointF(r.right(), r.center().y()), "right": QPointF(r.left(), r.center().y()),
                "top": QPointF(r.center().x(), r.bottom()), "bottom": QPointF(r.center().x(), r.top())}[side]

    def hoverEnterEvent(self, ev):
        self.hover = True
        self.update()
        super().hoverEnterEvent(ev)

    def hoverLeaveEvent(self, ev):
        self.hover = False
        self.update()
        super().hoverLeaveEvent(ev)

    def mousePressEvent(self, ev):
        self.on_click(self.node)
        super().mousePressEvent(ev)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.retrace()
        return super().itemChange(change, value)


class BoardItem(QGraphicsItem):
    def __init__(self, board):
        super().__init__()
        self.board = board
        self.w, self.h = (300, 330) if board["main"] else (230, 120)

    def boundingRect(self):
        return QRectF(0, 0, self.w, self.h)

    def paint(self, p, _opt, _widget=None):
        b = self.board
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor("#10251c" if b["main"] else "#1b1f2a")))
        pen = QPen(QColor("#2ea043" if b["main"] else "#8b949e"), 2)
        if b["off"]:
            pen.setStyle(Qt.DashLine)
            pen.setColor(QColor("#6e7681"))
        p.setPen(pen)
        p.drawRoundedRect(self.boundingRect().adjusted(1, 1, -1, -1), 14, 14)
        p.setPen(QColor("#e6edf3") if not b["off"] else QColor("#6e7681"))
        f = QFont("Segoe UI", 12)
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(14, 14, self.w - 28, 46), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, b["name"])
        p.setFont(QFont("Segoe UI", 8))
        p.setPen(QColor("#8b949e"))
        info = b["mcu"] or ""
        if b["off"]:
            info = (info + "  ·  " + tr("map.off")).strip(" ·")
        p.drawText(QRectF(14, 62, self.w - 28, 16), Qt.AlignHCenter, info)
        if b["detail"]:
            p.setFont(QFont("Consolas", 7))
            p.drawText(QRectF(10, 82, self.w - 20, 30), Qt.AlignHCenter | Qt.TextWordWrap, b["detail"])
        if b["main"]:
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor("#6e7681"))
            for label, rect in ((tr("map.side_motors"), QRectF(8, self.h / 2 - 8, 90, 16)),
                                (tr("map.side_heat"), QRectF(self.w / 2 - 45, 118, 90, 16)),
                                (tr("map.side_fans"), QRectF(self.w - 98, self.h / 2 - 8, 90, 16)),
                                (tr("map.side_sensors"), QRectF(self.w / 2 - 45, self.h - 26, 90, 16))):
                p.drawText(rect, Qt.AlignCenter, label)

    def port(self, side):
        r = self.sceneBoundingRect()
        return {"left": QPointF(r.left(), r.center().y()), "right": QPointF(r.right(), r.center().y()),
                "top": QPointF(r.center().x(), r.top()), "bottom": QPointF(r.center().x(), r.bottom())}[side]


class EdgeItem(QGraphicsPathItem):
    def __init__(self, node_item, board_item, side, color, dashed, offset):
        super().__init__()
        self.node_item, self.board_item, self.side, self.offset = node_item, board_item, side, offset
        pen = QPen(QColor(color), 1.6)
        pen.setCapStyle(Qt.RoundCap)
        if dashed:
            pen.setStyle(Qt.DashLine)
            pen.setColor(QColor("#f85149"))
        self.setPen(pen)
        self.setZValue(-1)
        node_item.edges.append(self)
        self.retrace()

    def retrace(self):
        a = self.node_item.anchor(self.side)
        b = self.board_item.port(self.side)
        if self.side in ("left", "right"):
            b = QPointF(b.x(), b.y() + self.offset)
            c1, c2 = QPointF((a.x() + b.x()) / 2, a.y()), QPointF((a.x() + b.x()) / 2, b.y())
        else:
            b = QPointF(b.x() + self.offset, b.y())
            c1, c2 = QPointF(a.x(), (a.y() + b.y()) / 2), QPointF(b.x(), (a.y() + b.y()) / 2)
        path = QPainterPath(a)
        path.cubicTo(c1, c2, b)
        self.setPath(path)


class MapMixin:
    def page_map(self):
        w, v = self._page(tr("map.title"), tr("map.hint"))
        row = QHBoxLayout()
        add = QToolButton()
        add.setText("＋  " + tr("map.add"))
        add.setPopupMode(QToolButton.InstantPopup)
        self.map_add_menu = QMenu(add)
        add.setMenu(self.map_add_menu)
        self.map_add_menu.aboutToShow.connect(self._fill_map_menu)
        row.addWidget(add)
        for text, fn in ((tr("map.fit"), self._map_fit), (tr("map.export"), self.act_map_export)):
            b = QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)
        self.map_status = QLabel(objectName="hint")
        row.addWidget(self.map_status, 1)
        v.addLayout(row)

        legend = QHBoxLayout()
        for group, color in GROUP_COLOR.items():
            lab = QLabel("●  " + tr("map.group_" + group))
            lab.setStyleSheet("color:%s;" % color)
            legend.addWidget(lab)
        legend.addStretch(1)
        v.addLayout(legend)

        body = QHBoxLayout()
        self.map_scene = QGraphicsScene()
        self.map_view = QGraphicsView(self.map_scene)
        self.map_view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.map_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.map_view.setBackgroundBrush(QColor("#0d1117"))
        self.map_view.setMinimumHeight(560)
        self.map_view.wheelEvent = self._map_wheel
        body.addWidget(self.map_view, 1)

        side = QFrame(objectName="listBox")
        side.setFixedWidth(280)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(14, 12, 14, 12)
        self.map_sel_title = QLabel(tr("map.no_selection"), objectName="featureTitle")
        self.map_sel_title.setWordWrap(True)
        sl.addWidget(self.map_sel_title)
        self.map_sel_note = QLabel(objectName="hint")
        self.map_sel_note.setWordWrap(True)
        sl.addWidget(self.map_sel_note)
        self.map_form_holder = QWidget()
        self.map_form = QFormLayout(self.map_form_holder)
        self.map_form.setContentsMargins(0, 8, 0, 8)
        sl.addWidget(self.map_form_holder)
        self.map_open_btn = QPushButton(tr("map.open_page"))
        self.map_open_btn.setVisible(False)
        sl.addWidget(self.map_open_btn)
        sl.addStretch(1)
        body.addWidget(side)
        v.addLayout(body, 1)
        self._map_selected = None
        return w

    # ---------- drawing ----------
    def _fill_map(self):
        if not hasattr(self, "map_scene"):
            return
        data = wiring(self.P, self.board(), self.current_text or "")
        self.map_scene.clear()
        self._map_nodes = {}

        boards, main = {}, None
        for b in data["boards"]:
            item = BoardItem(b)
            self.map_scene.addItem(item)
            boards[b["id"]] = item
            if b["main"]:
                item.setPos(-item.w / 2, -item.h / 2)
                main = item
        bx, by = (main.w / 2, main.h / 2) if main else (150, 165)

        by_side = {"left": [], "right": [], "top": [], "bottom": [], "extra": []}
        for n in data["nodes"]:
            item = NodeItem(n, self._map_select)
            self.map_scene.addItem(item)
            self._map_nodes[n["id"]] = item
            side = SIDE.get(n["group"], "bottom")
            if any((pin.get("board") or "mcu") != "mcu" for pin in n["pins"]):
                side = "extra"
            by_side[side].append((item, side))

        gap, margin = 18, 150
        col_half = 0
        for side in ("left", "right"):
            items = [i for i, _s in by_side[side]]
            total = sum(i._h for i in items) + gap * max(0, len(items) - 1)
            col_half = max(col_half, total / 2)
            y = -total / 2
            x = -bx - margin - NODE_W if side == "left" else bx + margin
            for i in items:
                i.setPos(x, y)
                y += i._h + gap
        clear = max(by, col_half) + margin          # rows must clear the motor / fan columns
        bottom_y = clear
        for side in ("top", "bottom", "extra"):
            items = [i for i, _s in by_side[side]]
            rows = [items[k:k + 4] for k in range(0, len(items), 4)]
            for r, row in enumerate(rows):
                row_h = max([i._h for i in row] or [0])
                if side == "extra":                  # under the right column, next to its own board
                    x = bx + margin
                    y = bottom_y + gap * 4 + r * (row_h + gap)
                else:
                    x = -(len(row) * NODE_W + gap * max(0, len(row) - 1)) / 2
                    y = (-clear - row_h - r * (row_h + gap)) if side == "top" else (clear + r * (row_h + gap))
                for i in row:
                    i.setPos(x, y)
                    x += NODE_W + gap
                if side == "bottom":
                    bottom_y = max(bottom_y, y + row_h)

        # the extra boards sit next to the devices that use them
        ex = [i for i, _s in by_side["extra"]]
        x_extra = bx + margin + NODE_W + 220
        for b in data["boards"]:
            if b["main"]:
                continue
            item = boards[b["id"]]
            y = (sum(i.y() for i in ex) / len(ex)) if ex else (by + margin)
            item.setPos(x_extra, y - item.h / 2 + 40)
            x_extra += item.w + 60

        for nid, item in self._map_nodes.items():
            n = item.node
            side = "right" if item.x() > 0 else "left" if item.x() + NODE_W < 0 else \
                   ("top" if item.y() < 0 else "bottom")
            visible = [pin for pin in n["pins"] if not pin["role"].startswith("bus:")]
            for k, pin in enumerate(n["pins"]):
                target = boards.get(pin.get("board") or "", main)
                if target is None:
                    continue
                offset = (k - (len(n["pins"]) - 1) / 2) * 9
                edge_side = side if target is main else ("right" if item.x() < target.x() else "left")
                EdgeItem(item, target, edge_side, GROUP_COLOR.get(n["group"], "#8b949e"),
                         bool(pin.get("issue")), offset)
                if pin in visible and len(visible) <= 4:
                    label = QGraphicsSimpleTextItem(pin["pin"] or "—")
                    label.setFont(QFont("Consolas", 8))
                    label.setBrush(QColor("#f85149") if pin.get("issue") else QColor("#8b949e"))
                    a, b2 = item.anchor(edge_side), target.port(edge_side)
                    label.setPos((a.x() + b2.x()) / 2 - 20, (a.y() + b2.y()) / 2 - 14 + offset)
                    self.map_scene.addItem(label)

        bad = sum(1 for n in data["nodes"] if n["issues"])
        self.map_status.setText(tr("map.status", devices=len(data["nodes"]), boards=len(data["boards"]), problems=bad))
        self.map_status.setStyleSheet("color:%s;" % ("#f85149" if bad else "#8b949e"))
        self._map_fit()
        if self._map_selected in self._map_nodes:
            self._map_select(self._map_nodes[self._map_selected].node)

    def _map_fit(self):
        if not hasattr(self, "map_view"):
            return
        rect = self.map_scene.itemsBoundingRect().adjusted(-40, -40, 40, 40)
        self.map_view.setSceneRect(rect)
        self.map_view.resetTransform()
        view = self.map_view.viewport().rect()
        if rect.width() and rect.height():
            scale = min(view.width() / rect.width(), view.height() / rect.height())
            scale = max(0.35, min(scale, 1.0))   # never so small that the labels are unreadable
            self.map_view.scale(scale, scale)
            self.map_view.centerOn(0, 0)

    def _map_wheel(self, ev):
        factor = 1.15 if ev.angleDelta().y() > 0 else 1 / 1.15
        self.map_view.scale(factor, factor)

    # ---------- selection ----------
    def _map_select(self, node):
        self._map_selected = node["id"]
        self.map_sel_title.setText("%s  %s" % (node["icon"], node["label"]))
        notes = list(node["issues"]) or ([node["note"]] if node["note"] else [])
        self.map_sel_note.setText("\n".join(notes))
        self.map_sel_note.setStyleSheet("color:%s;" % ("#f85149" if node["issues"] else "#8b949e"))
        while self.map_form.rowCount():
            self.map_form.removeRow(0)
        editable = not node["id"].startswith("section:")
        for pin in node["pins"]:
            edit = QLineEdit(pin["pin"])
            edit.setLayoutDirection(Qt.LeftToRight)
            edit.setReadOnly(not editable)
            if editable:
                edit.editingFinished.connect(
                    lambda nid=node["id"], role=pin["role"], e=edit: self._map_set_pin(nid, role, e.text()))
            self.map_form.addRow(pin["label"], edit)
        self.map_open_btn.setVisible(True)
        if getattr(self, "_map_open_conn", None) is not None:
            self.map_open_btn.clicked.disconnect(self._map_open_conn)
        page = node["page"]
        self.map_open_btn.setText(tr("map.open_page") if editable else tr("map.open_files"))
        self._map_open_conn = self.map_open_btn.clicked.connect(
            lambda: self.goto_page("page_files" if not editable else page))

    def _map_set_pin(self, node_id, role, value):
        if set_pin(self.P, node_id, role, value):
            self._fill_map()
            self.do_generate()

    # ---------- add ----------
    def _fill_map_menu(self):
        m = self.map_add_menu
        m.clear()
        for mid in OPTIONAL_MOTORS:
            if not self.P["motors"][mid]["enabled"]:
                a = m.addAction("⚙️  " + tr("motors.add_" + mid))
                a.triggered.connect(lambda _=False, x=mid: self._map_add_motor(x))
        m.addSeparator()
        for fid in ("probe", "leds", "fil_sensor", "sensorless"):
            from ..features import feature_on
            if not feature_on(self.P, fid):
                a = m.addAction("＋  " + tr("feat.%s.title" % fid))
                a.triggered.connect(lambda _=False, f=fid: self._map_add_feature(f))
        m.addSeparator()
        for cid in ("adxl_pico", "adxl_board", "chamber_sensor", "case_light", "controller_fan", "button"):
            a = m.addAction("%s  %s" % (CATALOG[cid][0], tr("cat.%s.title" % cid)))
            a.triggered.connect(lambda _=False, c=cid: self._map_add_catalog(c))
        m.addSeparator()
        a = m.addAction("🗂️  " + tr("map.more_features"))
        a.triggered.connect(lambda: self.goto_page("page_features"))

    def _map_add_motor(self, mid):
        self.act_add_motor(mid)
        self._fill_map()
        self.do_generate()

    def _map_add_feature(self, fid):
        self.collect()
        set_feature(self.P, fid, True)
        self.refresh()
        self.do_generate()

    def _map_add_catalog(self, cid):
        self._add_catalog(cid)
        self._fill_map()
        self.goto_page("page_features")

    # ---------- export ----------
    def act_map_export(self):
        rect = self.map_scene.itemsBoundingRect().adjusted(-30, -30, 30, 30)
        img = QImage(int(rect.width() * 2), int(rect.height() * 2), QImage.Format_ARGB32)
        img.fill(QColor("#0d1117"))
        p = QPainter(img)
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.map_scene.render(p, target=QRectF(img.rect()), source=rect)
        p.end()
        name = (self.P.get("printer_name") or "printer").strip().replace(" ", "-").lower() + "-wiring.png"
        path, _ = QFileDialog.getSaveFileName(self, tr("map.export"), os.path.join(os.path.expanduser("~"), name),
                                              "PNG image (*.png)")
        if path:
            img.save(path)
            self._log(tr("map.exported", path=path))
