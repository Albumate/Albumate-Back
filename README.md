# Albumate-Back

앨범메이트 백엔드 


---
### Flask 코드 컨벤션

| 구분          | 규칙/예시                          |
| ------------- | ---------------------------------- |
| 클래스 이름   | PascalCase (`class UserModel:`)    |
| 함수/변수 이름| snake_case (`def get_user():`, `user_data`) |
| 파일(모듈)    | snake_case.py (`user_service.py`)  |
| 블루프린트    | snake_case (`bp = Blueprint('user_bp', __name__)`) |
| 템플릿 파일   | snake_case.html (`user_profile.html`) |
| 환경 변수     | UPPER_CASE (`SECRET_KEY`, `DATABASE_URL`) |
| DB 모델       | PascalCase (`class Post(db.Model):`) |
| 테스트 파일   | test_snake_case.py (`test_user_service.py`) |
  

### 커밋 룰
---

| 태그 이름 | 설명 |
| --- | --- |
| [Feat] | 새로운 기능을 추가할 경우 |
| [Fix] | 버그를 고친경우 |
| [Design] | xml 등 사용자 UI 디자인 변경 |
| [!HOTFIX] | 급하게 치명적인 버그를 고쳐야하는 경우 |
| [Style] | 코드 포맷 변경, 린트 수정, 코드 수정이 없는 경우 |
| [Comment] | 필요한 주석 추가 및 변경 |
| [Docs] | 문서를 수정한 경우 |
| [Test] | 테스트 추가, 테스트 리팩토링(프로덕션 코드 변경 X) |
| [Chore] | 빌드 태스트 업데이트, 패키지 매니저를 설정하는 경우(프로덕션 코드 변경 X) |
| [Rename] | 파일 혹은 폴더명을 수정하거나 옮기는 작업만인 경우 |
| [Remove] | 파일을 삭제하는 작업만 수행한 경우 |
| [Setting] | Gradle, Manifest 등 파일에 세팅 추가 |

예시) 

```python
- [Feat] 회원가입 기능 추가
- [Docs] Readme 수정
```
