import sys
from pathlib import Path

path = Path(sys.argv[1]).expanduser().resolve(strict=True)
if not path.is_file():
    raise FileNotFoundError(path)

with path.open('r') as f:
    filedata = f.read()

# openJPA 2.0.0
# newdata = filedata.replace("-SNAPSHOT","").replace("<version>3.0.1</version>","<version>3.0.0</version>")
# openjpa 1.0.0
# newdata = filedata.replace("-SNAPSHOT","").replace("<version>3.0.1</version>","<version>3.0.0</version>").replace("<source>1.4</source>","<source>1.5</source>").replace("<target>1.4</target>","<target>1.5</target>").replace("http://www.ibiblio.org/maven2","https://mvnrepository.com/repos/ibiblio-m2").replace("https://maven-repository.dev.java.net/nonav/repository","https://repository.jboss.org/nexus/content/groups/public")
newdata = filedata.replace("-SNAPSHOT", "").replace("<version>3.2.0</version>", "<version>3.2.1</version>").replace(
    "<goal>check</goal>", "<!-- <goal>check</goal> -->").replace("<ignoreErrors>false</ignoreErrors>",
                                                                 "<ignoreErrors>true</ignoreErrors>").replace(
    "<version>3.2.4</version>", "<version>3.2.5</version>").replace("<version>3.3.7</version>",
                                                                    "<version>3.3.9</version>").replace(
    "<package>org.apache.maven</package>", "").replace("<logo>/images/maven.gif</logo>", "").replace(
    "<shortDescription>Maven components parent</shortDescription>", "").replace(
    "<logo>/images/apache-maven-project.png</logo>", "").replace("<scm>", "<!-- <scm>").replace("</scm>",
                                                                                                "</scm> -->").replace(
    "<ciManagement>", "<!-- <ciManagement>").replace("</ciManagement>", "</ciManagement> -->").replace(
    "<version>RELEASE</version>", "")
# .replace("1.0-alpha-1","1.0-alpha-7")
# replace("<description>Maven components parent</description>","  <packaging>pom</packaging>\n  <description>Maven components parent</description>")


with path.open('w') as f:
    f.write(newdata)
