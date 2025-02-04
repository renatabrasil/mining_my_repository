from dataclasses import dataclass


@dataclass
class ExtensionsFile:
    CSV = '.csv'
    JAR = '.jar'
    JAVA = '.java'
    TXT = '.txt'


@dataclass
class CommonsConstantsUtils:
    PATH_SEPARATOR = '/'
    HYPHEN_SEPARATOR = '-'
    END_STR = '\n'
