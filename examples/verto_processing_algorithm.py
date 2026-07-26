#!/usr/bin/env python3
"""
Verto Online Processing algorithm.

Single-file QgsProcessingAlgorithm that reads point features, sends their
coordinates to the official IGM Verto Online API, and writes a transformed
point layer.

This file is meant to be executed with the generic headless runner bundled in
skill/qgis-headless/scripts/run_algorithm.py.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant


DEFAULT_ENDPOINT = "https://igmi.esercito.difesa.it/porta-magna/wps/volapi"
DEFAULT_USER = "openverto"
DEFAULT_KEY = "openverto"
MAX_COORD = 32000


def _geometry_to_point(geometry: QgsGeometry) -> QgsPointXY:
    if geometry.isEmpty():
        raise QgsProcessingException("Feature without geometry")

    if geometry.isMultipart():
        points = geometry.asMultiPoint()
        if not points:
            raise QgsProcessingException("Multipart geometry has no points")
        point = points[0]
        return QgsPointXY(point.x(), point.y())

    if geometry.type() != Qgis.GeometryType.Point:
        raise QgsProcessingException("Only point geometries are supported")
    point = geometry.asPoint()
    return QgsPointXY(point.x(), point.y())


def _post_json(endpoint: str, body: dict, timeout: float) -> dict:
    payload = json.dumps(body).encode("utf-8")
    request = Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "qgis-headless-verto-processing",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    # The Verto endpoint sometimes prepends a debug log line (e.g. an SQL
    # INSERT statement) before the actual JSON body, so parse from the
    # first '{' rather than assuming the whole body is valid JSON.
    start = raw.find("{")
    if start == -1:
        raise QgsProcessingException("Verto response did not contain a JSON object")
    return json.loads(raw[start:])


def _convert_chunk(endpoint: str, in_epsg: int, out_epsg: int, coords: list[tuple[float, float]], timeout: float) -> list[tuple[float, float]]:
    body = {
        "richiesta": "conversione",
        "utente": DEFAULT_USER,
        "chiave": DEFAULT_KEY,
        "inEpsg": in_epsg,
        "outEpsg": out_epsg,
        "coordinate": [{"e": e, "n": n} for e, n in coords],
    }
    response = _post_json(endpoint, body, timeout)
    if response.get("stato") == "errore":
        dove = response.get("dove", "")
        messaggio = response.get("messaggio", "unknown error")
        raise QgsProcessingException(f"Verto error {dove}: {messaggio}".strip())

    output = response.get("coordinate", [])
    if len(output) != len(coords):
        raise QgsProcessingException(
            f"Verto returned {len(output)} coordinates for {len(coords)} input points"
        )
    return [(float(item["e"]), float(item["n"])) for item in output]


class VertoOnlinePointsAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    FROM_EPSG = "FROM_EPSG"
    TO_EPSG = "TO_EPSG"
    ENDPOINT = "ENDPOINT"
    TIMEOUT = "TIMEOUT"
    OUTPUT = "OUTPUT"

    def name(self) -> str:
        return "verto_online_points"

    def displayName(self) -> str:
        return "Verto Online points"

    def group(self) -> str:
        return "Examples"

    def groupId(self) -> str:
        return "examples"

    def shortHelpString(self) -> str:
        return (
            "Convert point coordinates with the official IGM Verto Online API "
            "and write the transformed points to an output sink."
        )

    def createInstance(self):
        return VertoOnlinePointsAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                "Point source layer",
                [QgsProcessing.TypeVectorPoint],
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.FROM_EPSG,
                "Source EPSG",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=3003,
                minValue=1,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TO_EPSG,
                "Target EPSG",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=6707,
                minValue=1,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.ENDPOINT,
                "Verto endpoint",
                defaultValue=DEFAULT_ENDPOINT,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TIMEOUT,
                "HTTP timeout (seconds)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=30.0,
                minValue=1.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                "Converted points",
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        from_epsg = self.parameterAsInt(parameters, self.FROM_EPSG, context)
        to_epsg = self.parameterAsInt(parameters, self.TO_EPSG, context)
        endpoint = self.parameterAsString(parameters, self.ENDPOINT, context).strip() or DEFAULT_ENDPOINT
        timeout = self.parameterAsDouble(parameters, self.TIMEOUT, context)

        fields = QgsFields(source.fields())
        fields.append(QgsField("verto_x", QVariant.Double))
        fields.append(QgsField("verto_y", QVariant.Double))
        fields.append(QgsField("verto_src", QVariant.Int))
        fields.append(QgsField("verto_dst", QVariant.Int))

        sink, sink_id = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.Point,
            QgsCoordinateReferenceSystem.fromEpsgId(to_epsg),
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        features = list(source.getFeatures())
        coords: list[tuple[float, float]] = []
        originals: list[QgsFeature] = []

        for index, feature in enumerate(features):
            if feedback.isCanceled():
                break
            point = _geometry_to_point(feature.geometry())
            coords.append((point.x(), point.y()))
            originals.append(feature)
            feedback.setProgress(int((index + 1) * 100 / max(1, len(features))))

        converted: list[tuple[float, float]] = []
        for start in range(0, len(coords), MAX_COORD):
            chunk = coords[start : start + MAX_COORD]
            converted.extend(_convert_chunk(endpoint, from_epsg, to_epsg, chunk, timeout))

        for feature, (x, y), (new_x, new_y) in zip(originals, coords, converted):
            new_feature = QgsFeature(fields)
            new_feature.setAttributes(
                feature.attributes()
                + [float(new_x), float(new_y), int(from_epsg), int(to_epsg)]
            )
            new_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(new_x, new_y)))
            sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: sink_id}
