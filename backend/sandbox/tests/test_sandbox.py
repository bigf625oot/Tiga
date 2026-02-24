import unittest
import os
import time
from e2b_code_interpreter import Sandbox

# Set E2B_API_KEY env var before running tests
# E2B_TEMPLATE_ID should point to your custom template built from Dockerfile

class TestCustomSandbox(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_key = os.environ.get("E2B_API_KEY")
        if not cls.api_key:
            raise unittest.SkipTest("E2B_API_KEY not set")
        
        # Connect to custom template (simulated by using default for now, but structure is correct)
        # In real usage: Sandbox(template="my-custom-template-id")
        cls.sandbox = Sandbox(api_key=cls.api_key) 

    @classmethod
    def tearDownClass(cls):
        if cls.sandbox:
            cls.sandbox.close()

    def test_01_file_operations(self):
        """Test creating, reading, and listing files"""
        print("\nRunning File Operation Test...")
        filename = "hello.txt"
        content = "Hello Sandbox!"
        
        # Write
        self.sandbox.files.write(filename, content)
        
        # Read
        read_content = self.sandbox.files.read(filename)
        self.assertEqual(read_content, content)
        
        # List
        files = self.sandbox.commands.run("ls -l").stdout
        self.assertIn(filename, files)

    def test_02_compilation_gcc(self):
        """Test GCC compilation"""
        print("\nRunning GCC Compilation Test...")
        c_code = """
        #include <stdio.h>
        int main() {
            printf("Hello C World");
            return 0;
        }
        """
        self.sandbox.files.write("main.c", c_code)
        
        # Compile
        compile_res = self.sandbox.commands.run("gcc main.c -o main_c")
        self.assertEqual(compile_res.exit_code, 0, f"Compilation failed: {compile_res.stderr}")
        
        # Run
        run_res = self.sandbox.commands.run("./main_c")
        self.assertEqual(run_res.stdout, "Hello C World")

    def test_03_compilation_java(self):
        """Test Java compilation"""
        print("\nRunning Java Compilation Test...")
        java_code = """
        public class Main {
            public static void main(String[] args) {
                System.out.println("Hello Java World");
            }
        }
        """
        self.sandbox.files.write("Main.java", java_code)
        
        # Compile
        compile_res = self.sandbox.commands.run("javac Main.java")
        self.assertEqual(compile_res.exit_code, 0, f"Compilation failed: {compile_res.stderr}")
        
        # Run
        run_res = self.sandbox.commands.run("java Main")
        self.assertEqual(run_res.stdout.strip(), "Hello Java World")

    def test_04_python_execution(self):
        """Test Python execution"""
        print("\nRunning Python Execution Test...")
        py_code = "print('Hello Python World')"
        run_res = self.sandbox.commands.run(f"python3 -c \"{py_code}\"")
        self.assertEqual(run_res.stdout.strip(), "Hello Python World")

    def test_05_node_execution(self):
        """Test Node.js execution"""
        print("\nRunning Node.js Execution Test...")
        js_code = "console.log('Hello Node World')"
        run_res = self.sandbox.commands.run(f"node -e \"{js_code}\"")
        self.assertEqual(run_res.stdout.strip(), "Hello Node World")

    def test_06_docker_check(self):
        """Test Docker installation"""
        print("\nRunning Docker Check Test...")
        # Note: Docker daemon might not be running unless explicitly started or dind is used
        # We just check client version here as requested by 'Toolchain' requirement
        res = self.sandbox.commands.run("docker --version")
        self.assertEqual(res.exit_code, 0)
        self.assertIn("Docker version", res.stdout)

if __name__ == '__main__':
    unittest.main()
