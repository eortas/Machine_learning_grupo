"""
Funciones para gestionar el repositorio Git
"""
import os
import logging
from git import Repo
from git.exc import GitCommandError

logger = logging.getLogger(__name__)


def inicializar_repo(repo_dir, repo_url, token):
    """
    Clona el repositorio si no existe o lo actualiza si ya existe.
    
    Args:
        repo_dir: Directorio local del repositorio
        repo_url: URL del repositorio
        token: Token de acceso a GitHub
        
    Returns:
        Repo: Objeto del repositorio Git
    """
    try:
        # Configura credenciales de Git
        os.environ['GIT_TERMINAL_PROMPT'] = '0'
        
        if not os.path.exists(repo_dir):
            # Construye URL con autenticación
            auth_url = f"https://{token}@{repo_url.replace('https://', '')}"
            logger.info(f"Clonando repositorio en {repo_dir}...")
            
            try:
                Repo.clone_from(auth_url, repo_dir, depth=1)  # depth=1 = clone rápido
            except GitCommandError as e:
                logger.error(f"Error en clone: {str(e)}")
                raise
        
        repo = Repo(repo_dir)
        
        # Configura Git user si no está configurado
        try:
            with repo.config_reader() as git_config:
                if not git_config.has_option("user", "email"):
                    repo.config_writer().set_value("user", "name", "ML Bot").release()
                    repo.config_writer().set_value("user", "email", "bot@ml.local").release()
        except Exception as e:
            logger.warning(f"No se pudo configurar git user: {e}")
        
        # Pull con manejo de errores
        try:
            logger.info("Haciendo pull del repositorio...")
            repo.remotes.origin.pull(force=True)  # force=True evita conflictos
        except GitCommandError as e:
            logger.warning(f"Pull falló, intentando reset: {str(e)}")
            try:
                # Intenta reset a origin/main o origin/master
                repo.git.fetch("origin", "main:main")
                repo.git.reset("--hard", "origin/main")
            except:
                try:
                    repo.git.fetch("origin", "master:master")
                    repo.git.reset("--hard", "origin/master")
                except GitCommandError as reset_error:
                    logger.warning(f"Reset también falló: {reset_error}")
                    # Continúa de todos modos - el repo local sigue siendo válido
        
        return repo
    
    except Exception as e:
        logger.error(f"Error inicializando repositorio: {str(e)}")
        raise


def commit_y_push(repo, mensaje_commit):
    """
    Realiza commit y push de los cambios al repositorio.
    
    Args:
        repo: Objeto del repositorio Git
        mensaje_commit: Mensaje del commit
        
    Returns:
        bool: True si fue exitoso, False en caso contrario
    """
    try:
        # Verifica si hay cambios antes de hacer commit
        if not repo.index.diff(None) and not repo.untracked_files:
            logger.info("No hay cambios para hacer commit")
            return True
        
        # Agrega archivos
        repo.git.add(".")
        
        # Verifica si hay cambios staged
        if repo.index.diff("HEAD"):
            # Realiza commit
            repo.index.commit(mensaje_commit)
            logger.info(f"Commit realizado: {mensaje_commit}")
        
        # Push con reintentos
        try:
            logger.info("Haciendo push...")
            origin = repo.remote(name="origin")
            origin.push(force=True)  # force=True para evitar rechazos
            logger.info("Push completado exitosamente")
            return True
        
        except GitCommandError as push_error:
            logger.error(f"Error en push: {str(push_error)}")
            # Intenta pull antes de push nuevamente
            try:
                logger.info("Intentando pull antes de push...")
                origin.pull(force=True)
                origin.push(force=True)
                logger.info("Push exitoso después de pull")
                return True
            except GitCommandError as retry_error:
                logger.error(f"Push falló incluso después de pull: {str(retry_error)}")
                return False
    
    except Exception as e:
        logger.error(f"Error en commit/push: {str(e)}")
        return False