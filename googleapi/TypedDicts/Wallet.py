from typing import TypedDict


class SubDefaultValueModel(TypedDict):
    language: str
    value: str


class DefaultValueModel(TypedDict):
    defaultValue: SubDefaultValueModel


class VenueModel(TypedDict):
    name: DefaultValueModel
    address: DefaultValueModel


class DateTimeModel(TypedDict):
    start: str


class SourceUriModel(TypedDict):
    uri: str


class ContentDescriptionModel(TypedDict):
    defaultValue: SubDefaultValueModel


class LogoModel(TypedDict):
    sourceUri: SourceUriModel
    contentDescription: DefaultValueModel


class EventClassModel(TypedDict):
    id: str
    eventName: DefaultValueModel
    issuerName: str
    reviewStatus: str
    logo: LogoModel
    dateTime: DateTimeModel
    venue: VenueModel


class HeroImageClass(TypedDict):
    sourceUri: SourceUriModel
    contentDescription: DefaultValueModel


class BarCodeModel(TypedDict):
    type: str
    value: str


class SubValidTimeIntervalModel(TypedDict):
    date: str


class ValidTimeIntervalModel(TypedDict):
    start: SubValidTimeIntervalModel
    end: SubValidTimeIntervalModel


class EventObjectModel(TypedDict):
    id: str
    classId: str
    state: str
    heroImage: HeroImageClass
    barcode: BarCodeModel
    hexBackgroundColor: str
    validTimeInterval: ValidTimeIntervalModel
    ticketNumber: str
