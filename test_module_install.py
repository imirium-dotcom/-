from module_manager import install_package


TEST_PACKAGE = "colorama"


print("================================")
print("   TEST MODULE INSTALLATION")
print("================================")
print()

print(f"Проверяем библиотеку: {TEST_PACKAGE}")
print()

result = install_package(TEST_PACKAGE)

print()
print("Результат:")
print(result)
print()

if result["success"]:
    print("ТЕСТ УСПЕШЕН.")
else:
    print("ТЕСТ НЕ ПРОЙДЕН.")