    def find_image_for_question(self, images_dir, question_number):
        """
        Поиск изображения для вопроса по номеру.
        Формат: 1.jpg, 01.jpg, 001.jpg, 2.png, 02.png и т.д.
        """
        images_path = Path(images_dir)

        if not images_path.exists():
            return None

        # Варианты форматирования номера: 1, 01, 001
        number_formats = [
            str(question_number),              # 1
            f"{question_number:02d}",          # 01
            f"{question_number:03d}",          # 001
        ]

        # Расширения файлов
        extensions = ['.jpg', '.jpeg', '.png', '.gif']

        # Проверяем все комбинации
        for num_format in number_formats:
            for ext in extensions:
                image_file = images_path / f"{num_format}{ext}"
                if image_file.exists():
                    return str(image_file)

        return None
