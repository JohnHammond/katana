import subprocess

from katana import units

DEPENDENCIES = ['zsteg']
permutations = list(
    {"b1,rgb,lsb,xy", "b1,r,lsb,xy", "b1,rgb,msb,yx", "b2,rgb,lsb,yx", "b2,rgb,lsb,xy", "b1,rgba,lsb,xy", "b1,r,lsb,xy",
     "b1,rgba,msb,yx", "b2,rgba,lsb,yx", "b2,rgba,lsb,xy"})


# permutations = list(set([ "b1,rgb,lsb,xy", "b1,r,lsb,xy", "b1,rgb,msb,yx", "b2,r,msb,yx", "b2,g,lsb,yx", "b2,b,lsb,yx", "b2,b,msb,yx", "b2,rgb,lsb,yx", "b2,rgb,msb,yx", "b2,bgr,lsb,yx", "b2,bgr,msb,yx", "b3,r,lsb,yx", "b3,r,msb,yx", "b4,g,lsb,yx", "b4,b,lsb,yx", "b4,rgb,lsb,yx", "b6,b,lsb,yx", "b7,g,msb,yx", "b8,g,msb,yx", "b2,bgr,lsb,yx,prime", "b3,r,lsb,yx,prime", "b4,bgr,lsb,yx,prime", "b5,r,lsb,yx,prime", "b8,g,lsb,yx,prime", "b2,r,msb,XY", "b2,g,lsb,XY", "b2,g,msb,XY", "b2,b,lsb,XY", "b2,b,msb,XY", "b2,rgb,lsb,XY", "b2,rgb,msb,XY", "b2,bgr,lsb,XY", "b2,bgr,msb,XY", "b3,r,lsb,XY", "b4,g,lsb,XY", "b4,b,lsb,XY", "b4,rgb,lsb,XY", "b8,b,lsb,XY", "b8,bgr,lsb,XY", "b1,r,msb,XY,prime", "b1,g,msb,XY,prime", "b2,r,msb,XY,prime", "b2,g,lsb,XY,prime", "b2,g,msb,XY,prime", "b2,b,lsb,XY,prime", "b2,b,msb,XY,prime", "b2,rgb,lsb,XY,prime", "b2,rgb,msb,XY,prime", "b2,bgr,lsb,XY,prime", "b2,bgr,msb,XY,prime", "b3,r,lsb,XY,prime", "b4,rgb,lsb,XY,prime", "b4,bgr,lsb,XY,prime", "b5,r,lsb,XY,prime", "b2,r,msb,YX", "b2,g,lsb,YX", "b2,g,msb,YX", "b2,b,lsb,YX", "b2,b,msb,YX", "b2,rgb,lsb,YX", "b2,rgb,msb,YX", "b2,bgr,lsb,YX", "b2,bgr,msb,YX", "b3,r,lsb,YX", "b4,r,msb,YX", "b4,g,msb,YX", "b4,b,msb,YX", "b4,rgb,msb,YX", "b4,bgr,lsb,YX", "b5,r,lsb,YX", "b8,g,lsb,YX", "b8,b,lsb,YX", "b8,rgb,lsb,YX", "b8,bgr,lsb,YX", "b1,r,lsb,YX,prime", "b1,rgb,msb,YX,prime", "b1,bgr,msb,YX,prime", "b2,rgb,msb,YX,prime", "b2,bgr,lsb,YX,prime", "b2,bgr,msb,YX,prime", "b3,r,lsb,YX,prime", "b1,r,msb,Xy,prime", "b1,g,msb,Xy,prime", "b1,b,msb,Xy,prime", "b4,r,msb,yX", "b4,g,msb,yX", "b4,b,msb,yX", "b2,r,msb,xY", "b2,g,lsb,xY", "b2,g,msb,xY", "b2,b,lsb,xY", "b2,b,msb,xY", "b2,rgb,lsb,xY", "b2,rgb,msb,xY", "b2,bgr,lsb,xY", "b2,bgr,msb,xY", "b3,r,lsb,xY", "b4,g,lsb,xY", "b4,b,lsb,xY", "b4,rgb,lsb,xY", "b4,bgr,lsb,xY", "b8,b,lsb,xY", "b2,r,msb,xY,prime", "b2,rgb,msb,xY,prime", "b2,bgr,lsb,xY,prime", "b2,bgr,msb,xY,prime", "b3,r,lsb,xY,prime", "b4,g,lsb,xY,prime", "b4,b,lsb,xY,prime", "b4,rgb,lsb,xY,prime", "b4,bgr,lsb,xY,prime", "b5,r,lsb,xY,prime", "b2,r,lsb,Yx", "b2,g,lsb,Yx", "b2,b,lsb,Yx", "b2,rgb,lsb,Yx", "b2,bgr,lsb,Yx", "b3,r,lsb,Yx", "b4,g,lsb,Yx", "b4,b,lsb,Yx", "b4,rgb,lsb,Yx", "b4,bgr,lsb,Yx", "b2,r,msb,Yx,prime", "b2,g,msb,Yx,prime", "b2,b,msb,Yx,prime", "b2,bgr,lsb,Yx,prime", "b3,r,lsb,Yx,prime", "b3,bgr,lsb,Yx,prime", "b4,r,lsb,Yx,prime", "b4,g,lsb,Yx,prime", "b4,b,lsb,Yx,prime", "b4,rgb,lsb,Yx,prime", "b4,bgr,lsb,Yx,prime", "b5,r,lsb,Yx,prime", "b1,r,lsb,xy", "b1,rgb,msb,xy", "b2,bgr,lsb,xy", "b3,r,lsb,xy", "b3,b,msb,xy", "b4,g,lsb,xy", "b4,b,lsb,xy", "b4,a,lsb,xy", "b4,bgr,lsb,xy", "b4,rgba,lsb,xy", "b7,b,lsb,xy", "b8,g,lsb,xy", "b8,b,lsb,xy", "b8,a,lsb,xy", "b8,bgr,lsb,xy", "b8,bgr,msb,xy", "b8,rgba,lsb,xy", "b4,g,lsb,xy,prime", "b4,b,lsb,xy,prime", "b4,a,lsb,xy,prime", "b4,bgr,lsb,xy,prime", "b4,rgba,lsb,xy,prime", "b5,r,lsb,xy,prime", "b5,g,msb,xy,prime", "b6,bgr,lsb,xy,prime", "b6,abgr,lsb,xy,prime", "b8,g,lsb,xy,prime", "b8,b,lsb,xy,prime", "b8,a,lsb,xy,prime", "b8,rgb,msb,xy,prime", "b8,bgr,lsb,xy,prime", "b8,rgba,lsb,xy,prime", "b2,rgba,msb,yx", "b3,b,msb,yx", "b4,g,lsb,yx", "b4,b,lsb,yx", "b4,a,lsb,yx", "b4,bgr,lsb,yx", "b4,rgba,lsb,yx", "b5,r,lsb,yx", "b5,b,lsb,yx", "b5,rgb,msb,yx", "b8,g,lsb,yx", "b8,b,lsb,yx", "b8,a,lsb,yx", "b8,bgr,lsb,yx", "b8,rgba,lsb,yx", "b2,g,lsb,yx,prime", "b2,bgr,lsb,yx,prime", "b2,rgba,lsb,yx,prime", "b3,r,lsb,yx,prime", "b3,bgr,msb,yx,prime", "b4,g,lsb,yx,prime", "b4,b,lsb,yx,prime", "b4,a,lsb,yx,prime", "b4,bgr,lsb,yx,prime", "b4,rgba,lsb,yx,prime", "b5,r,lsb,yx,prime", "b5,a,lsb,yx,prime", "b8,g,lsb,yx,prime", "b8,b,lsb,yx,prime", "b8,a,lsb,yx,prime", "b8,rgb,msb,yx,prime", "b8,bgr,lsb,yx,prime", "b8,bgr,msb,yx,prime", "b8,rgba,lsb,yx,prime", "b3,rgba,msb,XY", "b4,r,lsb,XY", "b4,g,lsb,XY", "b4,b,lsb,XY", "b4,a,lsb,XY", "b4,bgr,lsb,XY", "b4,rgba,lsb,XY", "b4,rgba,msb,XY", "b5,r,lsb,XY", "b5,g,msb,XY", "b7,r,lsb,XY", "b8,g,lsb,XY", "b8,b,lsb,XY", "b8,a,lsb,XY", "b8,bgr,lsb,XY", "b8,rgba,lsb,XY", "b2,b,lsb,XY,prime", "b3,r,lsb,XY,prime", "b4,r,lsb,XY,prime", "b4,r,msb,XY,prime", "b4,g,lsb,XY,prime", "b4,b,lsb,XY,prime", "b4,a,lsb,XY,prime", "b4,bgr,lsb,XY,prime", "b4,rgba,lsb,XY,prime", "b5,r,lsb,XY,prime", "b8,g,lsb,XY,prime", "b8,b,lsb,XY,prime", "b8,a,lsb,XY,prime", "b8,bgr,lsb,XY,prime", "b8,rgba,lsb,XY,prime", "b2,g,lsb,YX", "b2,rgb,msb,YX", "b2,rgba,lsb,YX", "b3,r,lsb,YX", "b3,b,lsb,YX", "b3,rgba,lsb,YX", "b4,r,lsb,YX", "b4,g,lsb,YX", "b4,b,lsb,YX", "b4,a,lsb,YX", "b4,bgr,lsb,YX", "b4,rgba,lsb,YX", "b5,r,lsb,YX", "b5,g,lsb,YX", "b5,b,lsb,YX", "b6,g,lsb,YX", "b6,rgba,lsb,YX", "b6,rgba,msb,YX", "b8,g,lsb,YX", "b8,b,lsb,YX", "b8,a,lsb,YX", "b8,bgr,lsb,YX", "b8,rgba,lsb,YX", "b2,b,lsb,YX,prime", "b2,rgba,lsb,YX,prime", "b3,a,lsb,YX,prime", "b4,r,lsb,YX,prime", "b4,g,lsb,YX,prime", "b4,b,lsb,YX,prime", "b4,a,lsb,YX,prime", "b4,bgr,lsb,YX,prime", "b4,rgba,lsb,YX,prime", "b7,r,lsb,YX,prime", "b7,b,lsb,YX,prime", "b8,g,lsb,YX,prime", "b8,b,lsb,YX,prime", "b8,a,lsb,YX,prime", "b8,bgr,lsb,YX,prime", "b8,rgba,lsb,YX,prime", "b2,g,msb,Xy", "b2,bgr,lsb,Xy", "b3,r,lsb,Xy", "b4,r,lsb,Xy", "b4,g,lsb,Xy", "b4,b,lsb,Xy", "b4,a,lsb,Xy", "b4,bgr,lsb,Xy", "b4,rgba,lsb,Xy", "b4,rgba,msb,Xy", "b5,r,lsb,Xy", "b5,b,lsb,Xy", "b8,g,lsb,Xy", "b8,b,lsb,Xy", "b8,a,lsb,Xy", "b8,bgr,lsb,Xy", "b8,bgr,msb,Xy", "b8,rgba,lsb,Xy", "b3,b,msb,Xy,prime", "b3,rgba,msb,Xy,prime", "b4,g,lsb,Xy,prime", "b4,b,lsb,Xy,prime", "b4,a,lsb,Xy,prime", "b4,bgr,lsb,Xy,prime", "b4,rgba,lsb,Xy,prime", "b5,r,lsb,Xy,prime", "b5,g,msb,Xy,prime", "b5,b,lsb,Xy,prime", "b8,g,lsb,Xy,prime", "b8,b,lsb,Xy,prime", "b8,a,lsb,Xy,prime", "b8,bgr,lsb,Xy,prime", "b8,rgba,lsb,Xy,prime", "b2,g,msb,yX", "b2,b,lsb,yX", "b2,a,lsb,yX", "b3,r,lsb,yX", "b4,r,msb,yX", "b4,g,lsb,yX", "b4,b,lsb,yX", "b4,a,lsb,yX", "b4,bgr,lsb,yX", "b4,rgba,lsb,yX", "b5,r,lsb,yX", "b5,a,lsb,yX", "b6,rgba,msb,yX", "b7,r,lsb,yX", "b8,g,lsb,yX", "b8,b,lsb,yX", "b8,b,msb,yX", "b8,a,lsb,yX", "b8,bgr,lsb,yX", "b8,rgba,lsb,yX", "b4,g,lsb,yX,prime", "b4,b,lsb,yX,prime", "b4,a,lsb,yX,prime", "b4,bgr,lsb,yX,prime", "b4,rgba,lsb,yX,prime", "b5,r,lsb,yX,prime", "b5,bgr,msb,yX,prime", "b7,r,lsb,yX,prime", "b8,g,lsb,yX,prime", "b8,b,lsb,yX,prime", "b8,a,lsb,yX,prime", "b8,bgr,lsb,yX,prime", "b8,bgr,msb,yX,prime", "b8,rgba,lsb,yX,prime", "b2,b,lsb,xY", "b3,g,lsb,xY", "b4,g,lsb,xY", "b4,b,lsb,xY", "b4,a,lsb,xY", "b4,bgr,lsb,xY", "b4,rgba,lsb,xY", "b5,r,lsb,xY", "b8,g,lsb,xY", "b8,b,lsb,xY", "b8,a,lsb,xY", "b8,rgb,msb,xY", "b8,bgr,lsb,xY", "b8,bgr,msb,xY", "b8,rgba,lsb,xY", "b2,a,lsb,xY,prime", "b3,r,lsb,xY,prime", "b4,g,lsb,xY,prime", "b4,b,lsb,xY,prime", "b4,a,lsb,xY,prime", "b4,bgr,lsb,xY,prime", "b4,rgba,lsb,xY,prime", "b5,r,lsb,xY,prime", "b5,bgr,msb,xY,prime", "b6,r,msb,xY,prime", "b6,g,msb,xY,prime", "b6,rgba,msb,xY,prime", "b8,g,lsb,xY,prime", "b8,b,lsb,xY,prime", "b8,a,lsb,xY,prime", "b8,rgb,msb,xY,prime", "b8,bgr,lsb,xY,prime", "b8,rgba,lsb,xY,prime", "b2,bgr,msb,Yx", "b3,b,msb,Yx", "b3,a,lsb,Yx", "b4,g,lsb,Yx", "b4,b,lsb,Yx", "b4,a,lsb,Yx", "b4,bgr,lsb,Yx", "b4,rgba,lsb,Yx", "b5,r,lsb,Yx", "b6,rgba,msb,Yx", "b8,g,lsb,Yx", "b8,b,lsb,Yx", "b8,a,lsb,Yx", "b8,bgr,lsb,Yx", "b8,rgba,lsb,Yx", "b4,r,msb,Yx,prime", "b4,g,lsb,Yx,prime", "b4,g,msb,Yx,prime", "b4,b,lsb,Yx,prime", "b4,a,lsb,Yx,prime", "b4,bgr,lsb,Yx,prime", "b4,rgba,lsb,Yx,prime", "b5,r,lsb,Yx,prime", "b5,g,msb,Yx,prime", "b7,r,lsb,Yx,prime", "b8,g,lsb,Yx,prime", "b8,b,lsb,Yx,prime", "b8,a,lsb,Yx,prime", "b8,bgr,lsb,Yx,prime", "b8,rgba,lsb,Yx,prime",]))

class Unit(units.FileUnit):
    PRIORITY = 40

    def __init__(self, katana, target):
        # This ensures it is a PNG
        super(Unit, self).__init__(katana, target, keywords=['png image'])
        self.completed = True

    def evaluate(self, katana, case):
        for args in permutations:

            p = subprocess.Popen(['zsteg', self.target.path, args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # p = subprocess.Popen(['zsteg', self.target, case ], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

            result = {
                "stdout": [],
                "stderr": [],
            }

            output = bytes.decode(p.stdout.read(), 'ascii')
            error = bytes.decode(p.stderr.read(), 'ascii')

            d = "\r"
            for line in output:
                s = [e + d for e in line.split(d) if e]

            for line in [l.strip() for l in output.split('\n') if l]:
                delimeter = '\r'
                lines = [e + d for e in line.split(d) if e]
                for temp_line in lines:
                    if not temp_line.endswith(".. \r"):
                        if katana.locate_flags(self, temp_line):
                            self.completed = True
                        result["stdout"].append(temp_line)

            for line in [l.strip() for l in error.split('\n') if l]:
                if katana.locate_flags(self, line):
                    pass
                result["stderr"].append(line)

            if not len(result['stderr']):
                result.pop('stderr')
            if not len(result['stdout']) or '[=] nothing :(\r' in result['stdout']:
                result.pop('stdout')

            katana.add_results(self, result)
