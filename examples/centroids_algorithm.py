#!/usr/bin/env python3
"""
Centroids Processing algorithm (offline example).

Single-file QgsProcessingAlgorithm that reads any vector layer and writes the
centroid of each feature to a point output layer. Unlike the Verto example it
needs no network access, so it doubles as the CI test for the generic headless
runner (skill/qgis-headless/scripts/run_algorithm.py).

Usage:
    QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
        python skill/qgis-headless/scripts/run_algorithm.py \
        --alg examples/centroids_algorithm.py \
        --params '{"INPUT": "examples/data/sample.geojson", "OUTPUT": "memory:"}'
"""
from __future__ import annotations

from qgis.core import (
    QgsFeature,
    QgsFeatureSink,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsWkbTypes,
)


class CentroidsAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    def name(self) -> str:
        return "centroids_example"

    def displayName(self) -> str:
        return "Centroids (offline example)"

    def group(self) -> str:
        return "Examples"

    def groupId(self) -> str:
        return "examples"

    def shortHelpString(self) -> str:
        return "Write the centroid of every input feature to a point layer."

    def createInstance(self):
        return CentroidsAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                "Input layer",
                [QgsProcessing.TypeVectorAnyGeometry],
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                "Centroids",
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        sink, sink_id = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            QgsWkbTypes.Point,
            source.sourceCrs(),
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        total = source.featureCount() or 1
        for index, feature in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                break
            geometry = feature.geometry()
            if geometry.isEmpty():
                feedback.pushWarning(f"Feature {feature.id()}: empty geometry, skipped")
                continue
            new_feature = QgsFeature(source.fields())
            new_feature.setAttributes(feature.attributes())
            new_feature.setGeometry(geometry.centroid())
            sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
            feedback.setProgress(int((index + 1) * 100 / total))

        return {self.OUTPUT: sink_id}
