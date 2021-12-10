from dataclasses import dataclass


@dataclass
class RegexConstants:
    SUBMITTED_BY__PARTICLE_REGEX = r'\Submitted\s*([bB][yY])[:]*\s*[\s\S][^\r\n]*[a-zA-Z0-9_.+-]+((\[|\(|\<)|(\s*(a|A)(t|T)\s*|@)[a-zA-Z0-9-]+(\s*(d|D)(O|o)(t|T)\s*|\.)[a-zA-Z0-9-.]+|(\)|\>|\]))'
    SUBMITTED_BY_SIMPLE__REGEX = r'\Submitted\s*([bB][yY])[:]*\s*'
    NAME_PATTERN__REGEX = r'\s*(\[|\(|\<)|[\sa-zA-Z0-9_.+-]+(\s*(a|A)(t|T)\s*|@)[a-zA-Z0-9-]+((\s*(d|D)(O|o)(t|T)\s*|\.)[a-zA-Z0-9-. ]+)+|(\)|\>|\])'
    FULL_EMAIL_PATTERN_REGEX = r'[\sa-zA-Z0-9_.+-]+(\s*(a|A)(t|T)\s*)[a-zA-Z0-9-]+((\s*(d|D)(O|o)(t|T)\s*)[a-zA-Z0-9-. ]+)+'
    EMAIL_PATTERN_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    COMMENTARY_REGEX = r'(\/\*([^*]|[\r\n]|(\*+([^*\/]|[\r\n]))){0,100}\*+\/)|\/{0,1}[^0-9][a-zA-Z]*\*[^;]([^0-9][a-zA-Z]+)[^\r\n]*'


@dataclass
class ProjectsConstants:
    ANT = 1
    LUCENE = 2
    MAVEN = 3
    OPENJPA = 4
    CASSANDRA = 5
    HADOOP = 6


@dataclass
class ConstantsUtils:
    TAG_DELIMITER = '*'
